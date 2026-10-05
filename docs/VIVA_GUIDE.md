# Viva and Demo Guide

## 1. The project in 30 seconds

> "I built an AI resume-screening and candidate-matching system in Python. I trained four machine-learning
> models and three deep-learning models on 2,481 real resumes in 24 job categories. A 1D convolutional
> neural network was the best single model, and an ensemble of the CNN and a Linear SVM reached 86%
> accuracy and 95% top-3 accuracy on resumes the models had never seen. The models drive an explainable
> match score between resumes and jobs, inside a Streamlit web app for candidates, employers and admins."

## 2. Key numbers to remember

| | |
| --- | --- |
| Dataset | 2,481 resumes, 24 categories, LiveCareer (CC0 licence) |
| Split | 1,984 train / 497 test (20%), plus a 15% validation slice of train |
| Best ML model | Linear SVM: 75.6% test accuracy |
| Best DL model | 1D-CNN: 81.9% ± 1.0% (3 seeds) |
| Deployed | SVM + CNN ensemble: **86.1% accuracy, 80.9% macro-F1, 95.2% top-3** |
| Matching | 87% of each job's top-10 candidates come from the job's category |
| Tests | 39 automated tests |

## 3. Five-minute demo script

Start `streamlit run app.py` before the examiner arrives. Every account uses the password `demo1234`.

| Step | Where | Do | Say |
| --- | --- | --- | --- |
| 1 | Resume Analyzer | Paste or upload a resume, click **Analyze** | "The ensemble predicts the category with a confidence; you can see the ML and DL models' individual answers, the top-5 probabilities, and the skills and experience extracted." |
| 2 | Resume Analyzer | Scroll to the matching jobs, open **Why this score?** | "Each match score breaks into four parts: category fit, skill match, CNN semantic similarity and experience." |
| 3 | Model Performance | Scroll through the table and charts | "All 7 models compared on the same unseen test set; deep models over 3 seeds. The deployed model was chosen on validation data." |
| 4 | Log in `ananya@example.com` → Recommended Jobs | Open a job, apply | "Candidates see every job ranked for them, with the skills they're missing." |
| 5 | Log in `talent@nimbus.example.com` → Ranked Applicants | Change a status to *Shortlisted* | "Employers see applicants sorted by AI score, with the explanation." |
| 6 | Find Candidates | Move the slider | "Employers can also search candidates who haven't applied." |
| 7 | Post a Job | Post a short job | "New jobs are matched immediately." |
| 8 | Log in `admin@example.com` | Dashboard, deactivate a user | "Admins manage users and see platform statistics." |
| 9 | Terminal | `python -m pytest` | "39 tests, including one that reloads the saved models and reproduces the reported accuracy." |

Have `notebooks/Resume_Screening_ML_DL.ipynb` open as a backup; it contains all outputs.

## 4. Likely questions and answers

### Data
1. **Where is the data from? Is it legal to use?** The LiveCareer resume dataset, published on Kaggle and
   Hugging Face under CC0 (public domain). Personal details were removed by the publisher, and my
   cleaning step removes any emails, links or phone numbers that remain.
2. **Why not the popular Kaggle resume dataset with 962 resumes?** Only 166 of its rows are unique. With a
   random split, copies of the same resume land in both training and test sets, so models score ~99%
   by memorising. That is data leakage, so I chose a dataset without it.
3. **What happened with your first dataset (the talent recruitment CSV)?** Every model scored ~33% on 3
   balanced classes, which is chance, and feature distributions were identical across classes. The labels
   had no relationship to the features, so I switched to real resume text. It's kept in `experiments/`.
4. **Is the data balanced?** Mostly, 100–120 resumes per category, but BPO has 22, Automobile 36 and
   Agriculture 63. I used stratified splits and report macro-F1 so small classes count equally.

### Preprocessing and features
5. **What preprocessing did you do?** Lowercase; remove personal data, symbols and extra spaces; keep
   tokens like `c++` and `node.js`; and repeat the first 8 words (the job-title headline) three times.
6. **Why repeat the headline?** Resumes start with the person's title, e.g. "STAFF ACCOUNTANT". Repeating
   it gives those words more weight. It raised SVM accuracy from about 68% to 74%; it is simple feature
   engineering.
7. **What is TF-IDF?** Term frequency × inverse document frequency: a word counts more if it is frequent
   in this resume but rare across all resumes. I used single words and word pairs, up to 50,000 features.

### Models
8. **Why did the CNN beat the other models?** Its convolution filters learn 5-word phrase detectors such as
   "accounts payable and receivable", and max pooling finds them anywhere in the resume. Categories are
   signalled by such local phrases, which TF-IDF only partly captures with word pairs.
9. **Why did the BiLSTM do worse?** Resumes are long (600 tokens); LSTMs are slower and harder to train on
   long sequences, and word order across the whole resume matters less than local phrases here. With
   ~1,700 training resumes it also overfits sooner.
10. **What is an embedding layer?** A trainable lookup table that turns each word ID into a 128-number
    vector; words used in similar contexts end up with similar vectors.
11. **How did you prevent overfitting?** Dropout (50%), early stopping on validation loss (patience 4,
    best weights restored), and a held-out test set. The training curves show training accuracy reaching
    ~99% while validation levels off near 80%, so early stopping matters.
12. **Why an ensemble?** The SVM (word statistics) and the CNN (learned phrases) make different mistakes;
    averaging their probabilities fixes some of each. Validation macro-F1: SVM 0.660, CNN 0.745,
    ensemble 0.757.
13. **Why not BERT?** Pre-trained transformers would likely do better, but they need large downloads and
    ideally a GPU. Training my own CNN shows the deep-learning process end to end and runs on any laptop.
    BERT / Sentence-BERT is my main future-work item.

### Evaluation
14. **How do you know the results aren't over-optimistic?** The test set (20%) was only used once, at the
    end. ML models were compared with 5-fold cross-validation on the training set; the deployed model was
    chosen on a separate validation slice. Deep models were run with 3 seeds and reported as mean ± std.
15. **What is macro-F1 and why report it?** F1 is the harmonic mean of precision and recall; macro-F1
    averages it equally over all 24 categories, so small categories like BPO aren't hidden by big ones.
16. **What is top-3 accuracy?** How often the true category is among the model's three most probable
    guesses: 95.2%. It matters because many resumes genuinely fit more than one category.
17. **Where does the model fail?** BPO (4 test resumes, F1 = 0), Automobile (F1 = 0.44), and overlapping
    careers: Apparel → Sales, Fitness → Sales, Finance → Accountant, Arts → Teacher.
18. **Are the demo candidates cherry-picked?** Partly, yes: each demo candidate uses the first test
    resume of their category that the model classifies correctly, so the demo is clear. The real error
    rate (about 14%) is on the Model Performance page.

### Matching
19. **How is the match score calculated?** 40% category probability, 30% share of required skills found,
    20% CNN embedding similarity, 10% experience fit. If experience is unknown, its weight is spread over
    the others.
20. **How did you evaluate matching without labels?** I treated a resume as relevant to a job when it is
    from the job's category, ranked all 497 test resumes for each of 24 jobs, and measured
    precision@10 and MAP. The final blend gets 87%; CNN embeddings (71%) beat TF-IDF similarity (58%).
21. **Why not just use the category probability, which scored 92%?** That benchmark defines relevance as
    category membership, so it naturally favours that signal. Employers also care about concrete skills
    and experience, which the benchmark can't measure, so they keep 40% of the weight.

### Engineering and ethics
22. **How are passwords stored?** Salted PBKDF2-HMAC-SHA256 hashes with 200,000 iterations, compared in
    constant time. Plain passwords are never stored.
23. **Why SQLite and Streamlit?** No server setup: the whole system runs with `streamlit run app.py`.
    For production I would move to PostgreSQL and a proper web framework.
24. **Could the model be biased?** Yes. Any model trained on historical resumes can learn biases in that
    data. That's why the score is explainable and meant to support, not replace, a recruiter. A fairness
    audit is in future work.

## 5. Files to have open

- `jobmatch/matcher.py`: the match-score formula
- `train.py`: all models and the evaluation protocol
- `jobmatch/text.py`: preprocessing
- `reports/figures/model_comparison.png` and `confusion_matrix.png`
- `notebooks/Resume_Screening_ML_DL.ipynb`
