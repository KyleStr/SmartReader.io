import rouge


def prepare_results(p, r, f):
    return '\t{}:\t{}: {:5.2f}\t{}: {:5.2f}\t{}: {:5.2f}'.format(metric, 'P', 100.0 * p, 'R', 100.0 * r, 'F1', 100.0 * f)


for aggregator in ['Avg', 'Best', 'Individual']:
    print('Evaluation with {}'.format(aggregator))
    apply_avg = aggregator == 'Avg'
    apply_best = aggregator == 'Best'

    evaluator = rouge.Rouge(metrics=['rouge-n', 'rouge-l', 'rouge-w'],
                           max_n=4,
                           limit_length=True,
                           length_limit=100,
                           length_limit_type='words',
                           apply_avg=apply_avg,
                           apply_best=apply_best,
                           alpha=0.5, # Default F1_score
                           weight_factor=1.2,
                           stemming=True)

    # Extractive summarization
    hypothesis_1 = "Ask the average American household today if they would have any problem spending extra money if productivity gains increased their incomes from $60K to $240K, and I pretty much guarantee you that most, except for a few simple-living hippies, would say, “No problem, man. This study has such a big number (but not a number so big as to seem unreasonable) that it is quoted in virtually every story on robots and jobs. For the risk of losing your job from your firm going out of business or downsizing in the next five years is more like 1,500 times greater than losing it to a robot."
    references_1 = "Some scientists have predicted that due to AI and Robotics an important amount of jobs will be eliminated worldwide. However, the author of the article argues why this techno-utopian/dstopian predictions are nonsensical. Firstly, productivity growth hasn't increased. Second, there is no relationship between higher productivity and unemployment. In fact the opposite is true, productivity leads to more money being spet therefore more jobs created. Finally because Moore's law is not a law and processor speed increases are slowing, while transistors able to be purchased per dollar are decreasing."
    # Abstractive summarization
    hypothesis_2 = "jobs will be eliminated in 20 years.  the prediction was made by mit scientist marvin minsky in 1970.  maybe robots replacing ceo’s is the answer to job security.  ai will help doctors make better diagnoses and treatment decisions; it won’t."
    references_2 = "Some scientists have predicted that due to AI and Robotics an important amount of jobs will be eliminated worldwide. However, the author of the article argues why this techno-utopian/dstopian predictions are nonsensical. Firstly, productivity growth hasn't increased. Second, there is no relationship between higher productivity and unemployment. In fact the opposite is true, productivity leads to more money being spet therefore more jobs created. Finally because Moore's law is not a law and processor speed increases are slowing, while transistors able to be purchased per dollar are decreasing."

    all_hypothesis = [hypothesis_1, hypothesis_2]
    all_references = [references_1, references_2]
    # all_hypothesis = [hypothesis_1]
    # all_references = [references_1]

    scores = evaluator.get_scores(all_hypothesis, all_references)

    for metric, results in sorted(scores.items(), key=lambda x: x[0]):
        if not apply_avg and not apply_best: # value is a type of list as we evaluate each summary vs each reference
            for hypothesis_id, results_per_ref in enumerate(results):
                nb_references = len(results_per_ref['p'])
                for reference_id in range(nb_references):
                    print('\tHypothesis #{} & Reference #{}: '.format(hypothesis_id, reference_id))
                    print('\t' + prepare_results(results_per_ref['p'][reference_id], results_per_ref['r'][reference_id], results_per_ref['f'][reference_id]))
            print()
        else:
            print(prepare_results(results['p'], results['r'], results['f']))
    print()