# ***********************
# ***********************
# GMV-SES DEIN Builder
# ***********************
# ***********************

# ** Sonar options
SONAR_OPTS ?=

# ***********************
# ***********************
# Tools configuration 
# ***********************
# ***********************

# ** Python
PYTHON ?= $(if $(PYTHON_VERSION),"$(shell which $(PYTHON_VERSION))","$(shell which python)")

# ** Virtualenv
VENV_NAME ?= venv
VENV_PATH = $(if $(VENV_BIN_ACTIVATE),$(VENV_NAME)/bin/activate,$(VENV_NAME)/Scripts/activate)
VENV_ACTIVATE ?= source
VENV_ACTIVATE += $(VENV_PATH)

# ** PyBuilder
PYB = $(VENV_ACTIVATE) && pyb

# ** Bump2Version
BUMP = $(VENV_ACTIVATE) && bump2version

# ** Sonar
SONAR = $(if $(SONAR_HOME),$(SONAR_HOME)/bin/sonar-scanner,sonar-scanner)
SONAR += $(if $(SONAR_OPTS),$(SONAR_OPTS),)

# ** Clair
CLAIR_SCANNER = clair-scanner
CLAIR_URL = http://dev-sec:6060
CLAIR_JENKINS_CALLBACK = $(shell hostname)
#CLAIR_THRESHOLD Valid values; 'Defcon1', 'Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown'
CLAIR_THRESHOLD ?= High
CLAIR_SCANNER_REPORTS_IMAGE = dev-tools.labs.gmv.com:5000/com.gmv.dein/clair-scanner-report:latest

# ** Docker
DOCKERFILE ?= docker/Dockerfile
DOCKER_REPO ?= dev-tools.labs.gmv.com:5000
DOCKER_LOGIN ?= docker login -u $(DOCKER_CREDS_USR) -p $(DOCKER_CREDS_PSW) $(DOCKER_REPO)
IMAGE_NAMESPACE = gmv-bda
IMAGE_NAME = smart-reader-app
IMAGE_VERSION ?= latest

# ***********************
# ***********************
# Makefile targets
# ***********************
# ***********************
help: ## Print this help.	
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

version: ## Obtain current (or BRANCH) version number
ifdef BRANCH
ifneq ($(shell git fetch --all 2>&1 >/dev/null && git rev-parse --verify --quiet $(BRANCH)),)
	@git show $(BRANCH):.bumpversion.cfg | grep '^current_version' | sed -r s,"^.*=\s*",,
else
	@echo "ERROR: Not exists branch '$(BRANCH)'"
endif
else
	@grep '^current_version' .bumpversion.cfg | sed -r s,"^.*=\s*",,
endif

venv: $(VENV_PATH)
$(VENV_PATH):
	test -d $(VENV_NAME) || $(PYTHON) -m venv $(VENV_NAME)
	$(VENV_ACTIVATE) && pip --version && python -m pip install pybuilder && python -m pip install --upgrade bump2version
	$(PYB) clean install_dependencies
	touch $(VENV_PATH)

clean_venv:
	if [ -d $(VENV_NAME) ]; then rm -rf $(VENV_NAME); fi

build: clean_venv venv ## Build the project
	@echo "[$@] Building project with version number $(shell make version)"
	$(PYB) compile_sources
	# build docker image
	make docker-build
	
test: venv ## Run unit test
	@echo "[$@] Running Unit test"
	$(PYB) run_unit_tests

qa: venv ## Run quality analysis
	@echo "[$@] Running SonarQube analysis"
	$(PYB) publish_distribution
	$(SONAR)

e2e: venv ## Run e2e test
	@echo "[$@] Running E2E test"
	$(PYB) verify publish_distribution

archive: ## Deploy docker image
	$(call check_defined, BRANCH_NAME, Required parameter missing)
ifeq ($(BRANCH_NAME), develop)
	@echo "[$@] Archive docker image"
	make docker-deploy TAG_VERSION=false TAG_NAME_LATEST=latest_develop
else
	@echo "[$@] Not archived docker image because branch is not develop"
endif

release-start: venv ## Create a new release with parameters RELEASE_VERSION && RELEASE_DEVELOP_VERSION
	$(call check_defined, RELEASE_VERSION, Required parameter missing)
	$(call check_defined, RELEASE_DEVELOP_VERSION, Required parameter missing)
	@echo "[$@] Starting the release $(RELEASE_VERSION)"
	@git checkout -b release/$(RELEASE_VERSION) develop
	@git checkout develop
	@$(BUMP) --new-version=$(RELEASE_DEVELOP_VERSION) minor
	@git checkout release/$(RELEASE_VERSION)
	@git push origin --all -u

release-finish: venv ## Finish a current hotfix branch
	@$(eval RELEASE_VERSION := $(shell git for-each-ref --format="%(refname:short)" refs/heads/release | tail -1 | sed 's/release\///g'))
	@$(eval RELEASE_DEVELOP_VERSION := $(shell make version BRANCH=develop))
	@echo "[$@] Finish release $(RELEASE_VERSION)"
	@git checkout develop
	@$(BUMP) --new-version=$(RELEASE_VERSION) release
	@git checkout release/$(RELEASE_VERSION)
	@$(BUMP) --new-version=$(RELEASE_VERSION) release
	@git checkout master
	@git merge --no-ff release/$(RELEASE_VERSION) -m "Merge release/$(RELEASE_VERSION) into master"
	@git tag -a $(RELEASE_VERSION) -m "Tag release $(RELEASE_VERSION)"
	@git checkout develop
	@git merge --no-ff release/$(RELEASE_VERSION) -m "Merge release/$(RELEASE_VERSION) into develop"
	@$(BUMP) --new-version=$(RELEASE_DEVELOP_VERSION) minor
	@git push origin --all -u
	@git push --tags
	@git branch -D release/$(RELEASE_VERSION)
	@git push origin -d -f release/$(RELEASE_VERSION)
	# build and deploy docker image on release
	git reset --hard $(RELEASE_VERSION)
	make docker-build IMAGE_VERSION=$(RELEASE_VERSION)
	make docker-deploy IMAGE_VERSION=$(RELEASE_VERSION) TAG_VERSION=true TAG_NAME_LATEST=latest
	@echo "[$@] Release $(RELEASE_VERSION) finished."

hotfix-start: venv ## Create a new hotfix branch with parameter RELEASE_VERSION
	$(call check_defined, RELEASE_VERSION, Required parameter missing)
	@echo "[$@] Starting the hotfix $(RELEASE_VERSION)"
	@git checkout -b hotfix/$(RELEASE_VERSION) master
	@$(BUMP) --new-version=$(RELEASE_VERSION).dev patch
	@git push origin --all -u

hotfix-finish: venv ## Finish a current hotfix branch
	@$(eval RELEASE_VERSION := $(shell git for-each-ref --format="%(refname:short)" refs/heads/hotfix | tail -1 | sed 's/hotfix\///g'))
	@$(eval RELEASE_DEVELOP_VERSION := $(shell make version BRANCH=develop))
	@echo "[$@] Finishing hotfix $(RELEASE_VERSION)"
	@git checkout develop
	@$(BUMP) --new-version=$(RELEASE_VERSION) release
	@git checkout hotfix/$(RELEASE_VERSION)
	@$(BUMP) --new-version=$(RELEASE_VERSION) release
	@git checkout master
	@git merge --no-ff hotfix/$(RELEASE_VERSION) -m "Merge hotfix/$(RELEASE_VERSION) into master"
	@git tag -a $(RELEASE_VERSION) -m "Tag hotfix $(RELEASE_VERSION)"
	@$(PYB) publish_distribution upload_distribution
	@git checkout develop
	@git merge --no-ff hotfix/$(RELEASE_VERSION) -m "Merge hotfix/$(RELEASE_VERSION) into develop"
	@$(BUMP) --new-version=$(RELEASE_DEVELOP_VERSION) minor
	@git push origin --all -u
	@git push --tags
	@git branch -D hotfix/$(RELEASE_VERSION)
	@git push origin -d -f hotfix/$(RELEASE_VERSION)
	# build and deploy docker image on hotfix
	git reset --hard $(RELEASE_VERSION)
	make docker-build IMAGE_VERSION=$(RELEASE_VERSION)
	make docker-deploy IMAGE_VERSION=$(RELEASE_VERSION) TAG_VERSION=true TAG_NAME_LATEST=latest
	@echo "[$@] Hotfix $(RELEASE_VERSION) finished."

docker-build: ## Build the docker image
ifneq ("$(wildcard $(DOCKERFILE))","")
	@echo "[$@] Docker image to build: $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)"
	@docker build --tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION) --build-arg HTTP_PROXY=$(http_proxy) --build-arg HTTPS_PROXY=$(http_proxy) --build-arg http_proxy=$(http_proxy) --build-arg https_proxy=$(http_proxy) -f $(DOCKERFILE) .
	@echo "[$@] Docker image built $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)"
endif

docker-deploy: ## Deploy the docker image
ifneq ("$(wildcard $(DOCKERFILE))","")
ifneq ($(shell docker images -q $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)),)
ifeq ($(TAG_VERSION),true)
	@echo "[$@] Found image $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)... Tagging with '$(IMAGE_VERSION)' and pushing to docker registry."
	@eval $(DOCKER_LOGIN)
	@docker tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION) $(DOCKER_REPO)/$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)
	@docker push $(DOCKER_REPO)/$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)
	@echo "[$@] Docker image deployed on $(DOCKER_REPO)/$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)"
else 
	@echo "[$@] Docker image NOT tagged with version"
endif
ifdef TAG_NAME_LATEST
	@echo "[$@] Found image $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)... Tagging with '$(TAG_NAME_LATEST)' and pushing to docker registry."
	@docker tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION) $(DOCKER_REPO)/$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(TAG_NAME_LATEST)
	@docker push $(DOCKER_REPO)/$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(TAG_NAME_LATEST)
	@echo "[$@] Docker image deployed on $(DOCKER_REPO)/$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(TAG_NAME_LATEST)"
else 
	@echo "[$@] Docker image NOT tagged with latest"
endif 
else
	@echo "[$@] Docker image NOT not found: $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)"
endif
else
	@echo "[$@] Docker file NOT not exists"
endif

deploy-jelastic: ## Redeploy on jelastic
	@echo "[$@] ReDeploying in Jelastic environment"
	$(eval TAG_VERSION=latest_develop)
ifeq ($(BRANCH_NAME), master)
	$(eval TAG_VERSION=latest)
endif
	curl -d "envName=$(JELASTIC_ENV_NAME)&session=$(JELASTIC_ACCESS_TOKEN)&nodeId=$(JELASTIC_NODE_ID)&tag=$(TAG_VERSION)" https://app.jelastic.labs.gmv.com/1.0/environment/control/rest/redeploycontainerbyid

clair-scanner: ## Scan Docker image for vulnerabilities and generate report
	$(call check_defined, CLAIR_REPORT_DIR, Required parameter missing)
	@echo "[$@] Starting Docker Container static Security Scan for $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)"
ifneq ($(shell docker images -q $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)),)
	@mkdir -p $(CLAIR_REPORT_DIR)
	@eval $(DOCKER_LOGIN)
	@docker pull $(CLAIR_SCANNER_REPORTS_IMAGE)
	$(CLAIR_SCANNER) --report="$(CLAIR_REPORT_DIR)/analysis-$(IMAGE_NAMESPACE)-$(IMAGE_NAME)-$(IMAGE_VERSION).json" --clair="$(CLAIR_URL)" --ip="$(CLAIR_JENKINS_CALLBACK)" --threshold="$(CLAIR_THRESHOLD)" $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION); CLAIR_RESULT=$$?; docker run -v $(CLAIR_REPORT_DIR):/clair-report $(CLAIR_SCANNER_REPORTS_IMAGE) --file /clair-report/analysis-$(IMAGE_NAMESPACE)-$(IMAGE_NAME)-$(IMAGE_VERSION).json --output /clair-report/index.html; exit $$CLAIR_RESULT
	@echo "[$@] Security scan finished, and report generated."
else
	@echo "[$@] Docker image NOT not found: $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_VERSION)"
endif

update: ## Update project files related with DEIN jobs from parent-pom git repo (master branch)
	@mkdir -p dein
	git archive --remote=git@dev-git.labs.gmv.com:gmv-dein/jenkins/pipelines.git master Jenkinsfile.ci Jenkinsfile.cd Jenkinsfile.mr Jenkinsfile.release Jenkinsfile.hotfix | tar xvf -
	@mv Jenkinsfile.ci dein/Jenkinsfile
	@mv Jenkinsfile.cd Jenkinsfile.mr Jenkinsfile.release Jenkinsfile.hotfix dein
	git archive --remote=git@dev-git.labs.gmv.com:gmv-dein/makefiles.git master Makefile.python | tar xvf -
	@mv Makefile.python Makefile

# ***********************
# ***********************
# Auxiliar functions 
# ***********************
# ***********************
# Check that given variables are set and all have non-empty values,
# die with an error otherwise.
#
# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
check_defined = \
	$(strip $(foreach 1,$1, \
		$(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
	$(if $(value $1),, \
		$(error Undefined $1$(if $2, ($2))))
