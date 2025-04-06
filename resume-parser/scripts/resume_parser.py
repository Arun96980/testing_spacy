import pdfplumber
import spacy
import re
from dateparser import parse as date_parse
from datetime import datetime
from collections import defaultdict
import json
import os
from tqdm import tqdm

class AdvancedResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        self._add_custom_patterns()
        
    def _add_custom_patterns(self):
        # Add patterns for technical terms
        ruler = self.nlp.add_pipe("entity_ruler", config={"validate": True})
        patterns = [
            {"label": "TECH", "pattern": [{"LOWER": {"IN": ["java", "python", "aws"]}}]},
            {"label": "TOOL", "pattern": [{"LOWER": {"IN": ["docker", "jenkins", "kubernetes"]}}]},
            {"label": "CERTIFICATION", "pattern": [{"LOWER": "certified"}, {"LOWER": {"REGEX": "^[a-z]+"}}]}
        ]
        ruler.add_patterns(patterns)

    def parse_resume(self, pdf_path):
        text = self._extract_text(pdf_path)
        doc = self.nlp(text)
        
        return {
            "summary": self._extract_summary(text),
            "total_experience": self._calculate_experience(doc),
            "skills": self._extract_skills(doc),
            "companies": self._extract_companies(doc),
            "positions": self._extract_positions(doc),
            "education": self._extract_education(text),
            "certifications": self._extract_certifications(doc),
            "tools": self._extract_tools(doc)
        }

    def _extract_text(self, pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages)

    def _extract_summary(self, text):
        # Find summary/objective section
        match = re.search(r"(summary|objective):?\s*(.*?)(?=\n\w+:|$)", 
                        text, re.IGNORECASE | re.DOTALL)
        return match.group(2).strip() if match else ""

    def _calculate_experience(self, doc):
        dates = []
        for ent in doc.ents:
            if ent.label_ == "DATE" and len(ent.text) > 4:
                try:
                    dates.append(date_parse(ent.text))
                except:
                    continue
        
        if len(dates) < 2:
            return 0
            
        dates = sorted([d for d in dates if d])
        if dates:
            return (dates[-1] - dates[0]).days // 365
        return 0

    def _extract_skills(self, doc):
        skills = set()
        # Noun chunks containing technical terms
        for chunk in doc.noun_chunks:
            if any(t.text.lower() in chunk.text.lower() for t in doc if t.pos_ == "VERB" and t.lemma_ in ["develop", "design", "build"]):
                skills.add(chunk.text)
        
        # Technical entities from custom NER
        skills.update(ent.text for ent in doc.ents if ent.label_ == "TECH")
        
        return list(skills)

    def _extract_companies(self, doc):
        companies = []
        current_company = None
        
        for sent in doc.sents:
            if " at " in sent.text:
                current_company = sent.text.split(" at ")[-1].split("(")[0].strip()
            if current_company and any(ent.label_ == "ORG" for ent in sent.ents):
                companies.append(current_company)
        
        return list(set(companies))

    def _extract_positions(self, doc):
        positions = []
        for ent in doc.ents:
            if ent.label_ == "TITLE" or (ent.root.dep_ == "attr" and "experience" in ent.text.lower()):
                positions.append(ent.text)
        return list(set(positions))

    def _extract_education(self, text):
        education = []
        edu_section = re.search(r"(education):?(.*?)(?=\n\w+:|$)", 
                               text, re.IGNORECASE | re.DOTALL)
        if edu_section:
            education = [line.strip() for line in edu_section.group(2).split('\n') if line.strip()]
        return education

    def _extract_certifications(self, doc):
        return list(set(ent.text for ent in doc.ents if ent.label_ == "CERTIFICATION"))

    def _extract_tools(self, doc):
        return list(set(ent.text for ent in doc.ents if ent.label_ == "TOOL"))

    def process_resumes(self, input_dir, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        for file in tqdm(os.listdir(input_dir)):
            if file.lower().endswith('.pdf'):
                try:
                    result = self.parse_resume(os.path.join(input_dir, file))
                    output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}.json")
                    with open(output_file, 'w') as f:
                        json.dump(result, f, indent=2)
                except Exception as e:
                    print(f"Error processing {file}: {str(e)}")

if __name__ == "__main__":
    parser = AdvancedResumeParser()
    parser.process_resumes(
        input_dir="input/resumes",
        output_dir="output/processed"
    )