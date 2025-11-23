Based on the JSON data you provided, I can see that your content is heavy on **filename patterns** (e.g., `syllabus_BSc_Physics_NEP_2025-26.pdf`) and **academic years**.

To make your search "Robust," you cannot rely on the user typing the exact filename. You need to handle the different ways students think.

Here is a breakdown of all the **Permutations and Combinations** you need to account for, organized by category.

### 1\. The "Semester" Logic (Numbers vs. Romans vs. Words)

Students are inconsistent with how they write numbers. Your search should treat all of these as identical.

| User Intent | Input Permutations (What they type) | Normalized Target (What code sees) |
| :--- | :--- | :--- |
| **First** | `1`, `I`, `i`, `1st`, `First`, `One` | **1** |
| **Second** | `2`, `II`, `ii`, `2nd`, `Second`, `Two` | **2** |
| **Third** | `3`, `III`, `iii`, `3rd`, `Third`, `Three` | **3** |
| **Fourth** | `4`, `IV`, `iv`, `4th`, `Fourth` | **4** |
| **Fifth** | `5`, `V`, `v`, `5th`, `Fifth` | **5** |
| **Sixth** | `6`, `VI`, `vi`, `6th`, `Sixth` | **6** |

**Recommendation:** Create a mapping function in JavaScript/Python that converts Roman numerals and words into integers (e.g., if user types "Sem III", search looks for "3").

### 2\. Course Name Variations (Punctuation & Spaces)

Your JSON uses `BSc`, `BCA`, `BA`, `BCom`. Students might add dots or spaces.

| JSON Standard | User Search Combinations |
| :--- | :--- |
| **BSc** | `B.Sc`, `B.Sc.`, `B Sc`, `Bachelor of Science`, `B.Science` |
| **BCom** | `B.Com`, `B.Com.`, `B Com`, `Commerce` |
| **BA** | `B.A`, `B.A.`, `B A`, `Arts` |
| **BCA** | `B.C.A`, `Computer Applications` |
| **PG** | `MSc`, `MA`, `Post Graduate`, `Masters` |

### 3\. Subject & Keyword Combinations (The "Mix & Match")

This is where the user combines Text + Number + Course.

**Scenario A: Syllabus Searching**

  * `Physics Syllabus`
  * `Syllabus Physics` (Order change)
  * `BSc Physics Syllabus` (Course + Subject + Type)
  * `Physics NEP` (Subject + Regulation)
  * `Physics 2025` (Subject + Year)

**Scenario B: Exam & Notices**

  * `Exam Date`
  * `Time table` vs `Timetable` vs `Date sheet`
  * `Admit Card` vs `Permission Letter`
  * `Results` vs `Mark sheet`

### 4\. Year/Session Variations

Your JSON contains filenames like `2025-26`, `2023-24`.

  * **User types:** `2025`
      * **Search should match:** `2025-26`, `2024-25` (Current context)
  * **User types:** `Previous year`
      * **Search should match:** `2023-24`, `2022-23`

-----

### 5\. Implementation Strategy (The Logic)

To handle these combinations without making your database massive, you should use a **Normalization Strategy** in your search logic.

Here is a logic map to visualize how to process the user's input before searching your JSON:

#### Example Code Logic (JavaScript Concept)

You can add this to your `index.html` script to "clean" the search query before filtering the JSON.

```javascript
function normalizeQuery(query) {
    let q = query.toLowerCase();

    // 1. Map Roman/Words to Numbers
    const numberMap = {
        'iii': '3', 'third': '3', '3rd': '3',
        'ii': '2', 'second': '2', '2nd': '2',
        'iv': '4', 'fourth': '4', '4th': '4',
        'i': '1', 'first': '1', '1st': '1',
        'v': '5', 'fifth': '5', '5th': '5',
        'vi': '6', 'sixth': '6', '6th': '6'
    };
    
    // Split text into words to check individually
    let words = q.split(' ');
    words = words.map(word => numberMap[word] || word);
    
    // 2. Normalize Courses (Remove dots)
    // e.g., "b.sc" becomes "bsc"
    q = words.join(' ').replace(/\./g, '');
    
    // 3. Handle Common Synonyms
    q = q.replace('timetable', 'time table');
    q = q.replace('sem ', 'semester ');

    return q; // Now "B.Sc. Physics Sem III" becomes "bsc physics sem 3"
}
```

### 6\. The "Smart Search" List

Based on your JSON, here are the most valuable combinations you should test your search bar with to ensure it works:

1.  **"BSc Physics 2025"** (Matches: `syllabus_BSc_Physics_NEP_2025-26.pdf`)
2.  **"Maths NEP"** (Matches: `Syllabus_BSc_Mathematics_wef_Oct2023.pdf` or similar)
3.  **"Exam Rules"** (Matches: `Examination-Ordinance-2024.pdf`)
4.  **"Fee Structure"** (Matches: `FEE-SCHEDULE-2025-26.pdf`)
5.  **"Holidays"** or **"Calendar"** (Matches: `Academic-Calendar2025-26.pdf`)

By implementing the **Normalization** step (Step 5), you cover 90% of the permutations (Roman numerals, dots in abbreviations, and synonyms) without having to hard-code every single possibility.
