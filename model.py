import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, roc_auc_score
from catboost import CatBoostClassifier
import warnings
warnings.filterwarnings('ignore')

BASE = '/root/.claude/uploads/1794bd6a-4cae-59d2-9509-d5a89c6c2a54/'
train = pd.read_csv(BASE + 'c328ced5-train_1.csv')
test = pd.read_csv(BASE + 'e794f84f-test_1.csv')

TARGET = 'Drafted'
drills = ['Sprint_40yd', 'Vertical_Jump', 'Bench_Press_Reps',
          'Broad_Jump', 'Agility_3cone', 'Shuttle']

def base_fe(df):
    df = df.copy()
    df['drills_done'] = df[drills].notna().sum(axis=1)
    for c in drills + ['Age']:
        df[c + '_missing'] = df[c].isna().astype(int)
    df['bmi'] = df['Weight'] / (df['Height'] ** 2)
    df['weight_per_height'] = df['Weight'] / df['Height']
    df['speed_score'] = df['Weight'] / (df['Sprint_40yd'] ** 4) * 200
    df['explosive'] = df['Vertical_Jump'].fillna(df['Vertical_Jump'].median()) \
                      + df['Broad_Jump'].fillna(df['Broad_Jump'].median()) / 10
    return df

train = base_fe(train)
test = base_fe(test)

# Position-relative z-scores (train stats only -> no leakage)
for c in drills + ['Height', 'Weight', 'bmi']:
    stats = train.groupby('Position')[c].agg(['mean', 'std'])
    for df in (train, test):
        m = df['Position'].map(stats['mean'])
        s = df['Position'].map(stats['std']).replace(0, np.nan)
        df[c + '_posz'] = (df[c] - m) / s

cat_cols = ['School', 'Player_Type', 'Position_Type', 'Position']
posz_cols = [c + '_posz' for c in drills + ['Height', 'Weight', 'bmi']]
num_cols = ['Year', 'Age', 'Height', 'Weight'] + drills + \
           ['drills_done', 'bmi', 'weight_per_height', 'speed_score', 'explosive'] + \
           [c + '_missing' for c in drills + ['Age']] + posz_cols
feat_cols = num_cols + cat_cols
y = train[TARGET].values

for c in cat_cols:
    train[c] = train[c].astype(str)
    test[c] = test[c].astype(str)

X, Xtest = train[feat_cols], test[feat_cols]
cat_idx = [feat_cols.index(c) for c in cat_cols]

def make_model():
    return CatBoostClassifier(
        iterations=2000, learning_rate=0.025, depth=6, l2_leaf_reg=6.0,
        random_strength=1.0, bagging_temperature=1.0, border_count=128,
        cat_features=cat_idx, loss_function='Logloss', eval_metric='AUC',
        random_seed=42, verbose=0)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
oof = np.zeros(len(X)); test_proba = np.zeros(len(Xtest)); fold_auc = []
for tr, va in cv.split(X, y):
    m = make_model()
    m.fit(X.iloc[tr], y[tr], eval_set=(X.iloc[va], y[va]),
          use_best_model=True, early_stopping_rounds=100)
    oof[va] = m.predict_proba(X.iloc[va])[:, 1]
    test_proba += m.predict_proba(Xtest)[:, 1] / cv.n_splits
    fold_auc.append(roc_auc_score(y[va], oof[va]))

cv_auc = roc_auc_score(y, oof)
print('=== CatBoost 5-fold CV ===')
print('ROC-AUC        : %.4f  (folds: %s)' % (cv_auc, ', '.join('%.3f' % a for a in fold_auc)))
print('Accuracy @0.5  : %.4f' % accuracy_score(y, (oof >= 0.5).astype(int)))

best_t, best_a = 0.5, 0
for t in np.linspace(0.2, 0.8, 241):
    a = accuracy_score(y, (oof >= t).astype(int))
    if a > best_a:
        best_a, best_t = a, t
print('Accuracy (tuned): %.4f @ threshold %.3f' % (best_a, best_t))

# --- Submissions ---
# Class-label submission (matches sample_submission format)
sub = pd.DataFrame({'Id': test['Id'], 'Drafted': (test_proba >= best_t).astype(int)})
sub.to_csv('/home/user/codebase-memory-mcp/submission.csv', index=False)
# Probability submission (use if the metric is AUC / ROC)
sub_p = pd.DataFrame({'Id': test['Id'], 'Drafted': test_proba})
sub_p.to_csv('/home/user/codebase-memory-mcp/submission_proba.csv', index=False)

print('\nsubmission.csv        :', sub.shape, dict(sub['Drafted'].value_counts()))
print('submission_proba.csv  : probability version saved')
