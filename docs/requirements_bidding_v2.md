# Bidding Assistant V2 Requirements & Roadmap

## 1. Core Philosophy
**"SaveTime (省点事)"**: The tool is a lightweight assistant, not a rigid scoring machine.
- **Primary Goal**: Help sales quickly check if they meet the *hard requirements* (Case, Qualification, Personnel).
- **Secondary Goal**: Provide "AI Insights" like estimated score, disqualifiers, and timeline as helpful tips.

## 2. Functional Requirements

### A. Requirement Matching (The Core)
The system must extract requirements from the uploaded tender document and match them against the internal database.

#### 1. Case Requirements (业绩要求)
- **Input**: Tender document text.
- **Extraction**: Extract specific project experience requirements (e.g., "3 similar projects in the last 3 years", "Contract value > 5M").
- **Matching**: Query `contracts.db` (`contracts` table) using keywords.
- **Output**:
    - **Status**: Satisfied (✅) / Unsatisfied (❌) / Manual Check (⚠️).
    - **Evidence**: List matched contract titles and amounts.

#### 2. Qualification Requirements (资质要求)
- **Input**: Tender document text.
- **Extraction**: Extract required company certifications or software copyrights (e.g., "CMMI5", "ISO9001", "Software Copyright for X").
- **Matching**: Query `contracts.db` (`assets` table) using fuzzy matching.
- **Output**:
    - **Status**: Satisfied (✅) / Unsatisfied (❌).
    - **Evidence**: Name of the matched asset.

#### 3. Personnel Requirements (人员要求)
- **Input**: Tender document text.
- **Extraction**: Extract key personnel requirements (e.g., "Project Manager with PMP", "Technical Director with Senior Title").
- **Matching**: *Currently Manual*. No personnel data in `contracts.db`.
- **Output**:
    - **Status**: Manual Check (⚠️).
    - **Evidence**: "Need to check resumes manually".

### B. AI Insights (The "Tips")
These are displayed in a sidebar or secondary area to assist decision-making.

#### 1. Score Estimation
- If the tender contains a scoring table, estimate the score based on matched items.
- If no scoring table is found, display "No scoring standard found".

#### 2. Disqualifiers (废标项)
- Highlight critical "must-have" items that would cause immediate disqualification (e.g., "Missing financial audit", "Breach of contract record").

#### 3. Timeline
- Extract key dates: Bid Bond Payment, Submission Deadline, Opening Date.

## 3. UI/UX Requirements
- **Layout**: 
    - **Main Area**: 3 Distinct Cards for Case, Qualification, and Personnel.
    - **Sidebar**: AI Insights (Score, Disqualifiers, Timeline).
- **Interaction**:
    - Upload file -> Analyze -> Show Results.
    - Support PDF, Word, TXT.

## 4. TODO List

### Immediate (Current Sprint)
- [x] **Backend**: Implement `bidding_v2` service with new matching logic.
- [x] **Backend**: Update Pydantic schemas for `RequirementItem`.
- [x] **Frontend**: Redesign `index.html` with 3-card layout + sidebar.
- [x] **Frontend**: Update `app.js` to render new data structure.
- [ ] **Deployment**: Push changes to GitHub and verify on server.

### Future / Backlog
- [ ] **Personnel Data**: Import personnel data into `contracts.db` to enable automatic matching for personnel requirements.
- [ ] **Document Generation**: Implement "Generate Pre-qualification Doc", "Generate Quote", etc.
- [ ] **Deep Matching**: Improve keyword matching accuracy (use vector search/embeddings instead of simple SQL `LIKE`).
- [ ] **Feedback Loop**: Allow users to manually correct "Manual Check" items and save the result.
