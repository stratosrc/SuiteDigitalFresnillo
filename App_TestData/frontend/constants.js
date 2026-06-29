export const emptyHistory = () => ({ reserved: [], confidential: [], other_law: [] });

export const defaultRedactionForm = () => ({
  concept_id: "1",
  classification: "general",
  legal_basis: "",
  reason: "",
  rows: "1",
  paragraphs: "1",
  object: "",
  articles: "",
  law: "",
});
