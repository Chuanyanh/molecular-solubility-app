# Molecular Solubility Prediction — Research Report

Author: Chuanyan He

## 1. Objective

Predict aqueous molecular solubility from molecular structure
and compare a descriptor-based Random Forest model with a
GINE graph neural network.

The prediction target is logS: the base-10 logarithm of
solubility in mol/L.

## 2. Data and Evaluation

After canonical-structure deduplication, ESOL contained
1,106 molecules.

A scaffold-based split produced 920 training molecules
and 186 holdout molecules. Nonempty scaffolds were kept
separate across the split; acyclic molecules were grouped
by canonical structure.

The external evaluation used 6,578 filtered AqSolDB records.
Filtering included invalid structures, mixtures, charged
molecules, unsupported elements, ESOL structure overlap,
and internally duplicated tautomer groups.

A final structure audit found no overlap with ESOL under
exact, stereochemistry-removed, or canonical-tautomer
matching. This does not establish independence of all
underlying literature measurement sources.

## 3. Models

Random Forest used seven molecular descriptors:
molecular weight, logP, topological polar surface area,
hydrogen-bond donor count, hydrogen-bond acceptor count,
rotatable bond count, and ring count.

GINE used molecular graphs with atom and bond features.
The deployed model used seed 42 and was trained for
43 epochs on the 920-molecule training set.
The epoch count was selected using an inner validation split.

Three random seeds were evaluated on the same fixed split.
Their variation measures training randomness, rather than
uncertainty across different dataset splits.

## 4. Prediction Results

The following results compare Random Forest with the
deployed GINE model, seed 42. Errors are in logS units.

| Dataset | N | Model | MAE | RMSE |
|---|---:|---|---:|---:|
| ESOL scaffold holdout | 186 | Random Forest | 0.5969 | 0.8056 |
| ESOL scaffold holdout | 186 | GINE, seed 42 | 0.5471 | 0.7205 |
| AqSolDB external | 6578 | Random Forest | 0.8652 | 1.1770 |
| AqSolDB external | 6578 | GINE, seed 42 | 0.8736 | 1.2724 |

![Model comparison](model_comparison.png)

GINE performed better on the ESOL holdout.
Random Forest performed better than the deployed GINE
model on the external dataset.

Across three seeds, GINE had a mean external MAE of
0.8547 logS, with a sample standard deviation of 0.0222.
This average describes three separate models; it is not
the performance of an ensemble or the deployed model.

## 5. Prediction Intervals

Conformalized Quantile Regression (CQR) used a separate
descriptor-based interval model.

The 920 training molecules were divided into 459 fitting
molecules and 461 calibration molecules.
External measurements were not used for fitting or calibration.

| Dataset | Target coverage | Observed coverage | Mean width, logS |
|---|---:|---:|---:|
| ESOL holdout | 90% | 86.0% | 3.132 |
| AqSolDB external | 90% | 79.6% | 3.190 |

![Prediction interval coverage](interval_coverage.png)

External coverage fell below the target.
A nominal 90% target should not be interpreted as
demonstrated 90% coverage for arbitrary new molecules.

## 6. Application

The Streamlit application supports:

- Chemical-name and SMILES input
- PubChem structure lookup
- Molecular structure visualization
- Random Forest and GINE predictions
- logS and mg/L output
- Prediction intervals and training-domain checks
- Batch CSV prediction and export
- Manual experimental-value comparison
- Research results and supporting downloads

Live application:
https://chuanyanh-solubility.streamlit.app/

Repository:
https://github.com/Chuanyanh/molecular-solubility-app

## 7. Limitations

Temperature and pH are not explicit model inputs.
Recording these conditions in a manual comparison does
not adjust the model prediction.

Large molecules require particular caution. For the
48 external molecules exceeding the training maximum
of 55 atoms, GINE's mean MAE across three seeds was
approximately 4.008 logS.

The ESOL holdout was inspected during project development,
so it is not a newly collected blind test set.

Retrieved literature solubility values are exploratory
references. Their independence from the training and
evaluation sources has not been fully verified.

A single experimental value inside an interval does not
establish the interval's overall coverage.

## 8. Conclusion

The project provides a working molecular-solubility
prediction application with scaffold-based evaluation,
external testing, seed-stability analysis, prediction
intervals, and structure-domain diagnostics.

Results show that improved holdout accuracy does not
guarantee improved external performance. External
evaluation and explicit limitations are therefore
central to interpreting the predictions.
