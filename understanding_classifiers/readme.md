# What do the classifiers actually recognize?

Pubmed's thorough annotation with MeSH terms, together with the detailed annotation of the MeSH terms themselves, gives us excellent opportunities to characterize and try ot understand the relationships between the concepts recognized by the classifiers.

Here we focus on comparing _predictions_ of MeSH terms (represented by the coefficient vectors of logistic regression models) to _definitions_ of those terms (taken from the MeSH documentation, and represented by their semantic embeddings).
