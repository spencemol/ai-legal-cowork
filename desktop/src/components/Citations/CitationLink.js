import { jsxs as _jsxs } from "react/jsx-runtime";
export function CitationLink({ citation, index, onCitationClick }) {
    const pageInfo = citation.page !== null ? ` — p. ${citation.page}` : '';
    const titleText = `${citation.text_snippet}${pageInfo}`;
    return (_jsxs("button", { className: "citation-link", title: titleText, onClick: () => onCitationClick(citation), type: "button", children: ["[", index, "]"] }));
}
