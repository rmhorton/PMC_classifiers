# Generate Heatmap for Predicted MeSH Terms for Mechanisms of Action

library(dplyr)
library(readxl)

S_df <- read_excel("representative_drugs_selected_MeSH_term_scores.xlsx")

S <- S_df[-1] %>% as.matrix

dimnames(S)[1] <- S_df[1]

heatmap(S, col=palette)

pdf("representative_drugs_selected_MeSH_term_heatmap.pdf", width=160, height=80, pointsize=24)
palette <- colorRampPalette(c("red", "white", "blue"))(256)
(hv <- heatmap(S, margins=c(20, 40), cexCol=0.4, cexRow=0.6, col=palette))
dev.off()

