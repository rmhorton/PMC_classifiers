# What do the classifiers actually recognize?

## Examples of articles scored with a panel of models

These models were trained on MeSH terms added in 2022, and we use them on articles from 2015.

[new_descriptors_2015_big_df.xlsx](https://github.com/rmhorton/PMC_classifiers/blob/main/understanding_classifiers/new_descriptors_2015_big_df.xlsx)

## Model predictions on MeSH term Definitions
[top_20_definition_terms.xlsx](https://github.com/rmhorton/PMC_classifiers/blob/main/understanding_classifiers/top_20_definition_terms.xlsx)

Pubmed's thorough annotation with MeSH terms, together with the detailed annotation of the MeSH terms themselves, gives us excellent opportunities to characterize and try ot understand the relationships between the concepts recognized by the classifiers.

Here we focus on comparing _predictions_ of MeSH terms (represented by the coefficient vectors of logistic regression models) to _definitions_ of those terms (taken from the MeSH documentation, and represented by their semantic embeddings).
