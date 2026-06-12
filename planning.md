# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:*aFilters the mock datasets for relevant items*
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): ...
- `size` (str): ...
- `max_price` (float): ...

**What it returns:*A list of dictionary objects represneting clothing items *
<!-- Describe the return value — what fields does a result contain? -->

**What happens if it fails or returns nothing:*If no items match, return an empty list `[]`. The planning loop will detect this to prevent downstream errors.*
<!-- What should the agent do if no listings match? -->

---

### Tool 2: suggest_outfit

**What it does:*Generates styling adviced based on a new item and existing wardrobe *
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): ...
- `wardrobe` (dict): ...

**What it returns:* A formatted string containing outfit suggestions*
<!-- Describe the return value -->

**What happens if it fails or returns nothing:*If `wardrobe` is empty, the LLM should be prompted to provide general style tips instead of failing, returning a helpful string rather than an exception.*
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

---

### Tool 3: create_fit_card

**What it does:*Creates a social media-ready caption*
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): ...

**What it returns:*A creative, shareable caption (str).*
<!-- Describe the return value -->

**What happens if it fails or returns nothing:*If outfit is empty or None, return a default string: "Couldn't generate a fit card, but this item is a great find!"*
<!-- What should the agent do if the outfit data is incomplete? -->

---

### Additional Tools (if any)
## Price_Comparison
**What it does:*Determine if the item is a "good deal" by comparing its price to the average price of similar items (same category or style) in the dataset.

Inputs:*
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `item` (dict): ...
- `listings`
**What it returns:*A string indicating the result (e.g., "Fair Price," "Great Deal," or "Expensive") and a brief explanation (e.g., "This is 20% below the average price for similar vintage tees")*
<!-- Describe the return value -->

**What happens if it fails or returns nothing:*If no comparable listings exist (e.g., the category is unique), return "Insufficient data to determine price fairness."*
<!-- What should the agent do if the outfit data is incomplete? -->

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The planning loop operates sequentially. It first calls`search_listings` executes first. If no items match, the agent halts with a specific error message.

If an item is found, the agent proceeds to `price_comparison`, calculating if the item is a 'Great Deal' or 'Expensive' relative to the dataset.

This price verdict is stored in the session state.

`suggest_outfit` uses the selected item to generate style advice.

Finally, `create_fit_card` consumes the outfit suggestion and the stored price verdict to build a comprehensive caption. This ensures the user receives both style and financial value insights in the final output
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

     graph TD
    User([User Query]) --> Planner{Planning Loop}
    Planner -->|Search| Search[search_listings]
    
    Search -->|Results Found| State1[Store selected_item in Session]
    Search -->|Empty Results| Error1[Set Error Message & Exit]
    
    State1 --> Suggest[suggest_outfit]
    Suggest -->|Suggestion| State2[Store outfit_suggestion in Session]
    
    State2 --> Card[create_fit_card]
    Card -->|Fit Card| Final([Return Session State])

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->


**Milestone 3 — Individual tool implementations:*
- AI Tool: Claude 3.5 Sonnet,
- Strategy&Input: Provide `planning.md` tool specs. Prompt: "Implement this tool in   `tools.py` using `load_listings()`. Include strict type checking and handle the failure mode by returning an empty list/default string, not raising exceptions."
- Verification: Run `pytest tests/test_tools.py`. If any test fails, feed the error back to Claude.
*

**Milestone 4 — Planning loop and state management:*
 - AI Tool: Claude 3.5 Sonnet,
- Strategy&Input: Provide the `## Architecture` mermaid diagram and `## Planning Loop logic`. Prompt: "Implement run_agent() in agent.py. Ensure the logic halts execution if `search_listings` returns an empty list, and passes the `selected_item` and `price_verdict` through the session state
."
- Verification: Inspect `session` state with `print()` statements to verify data flow between tools.
*
**Milestone 5 — Error Handling:*
AI Tool: Gemini/copilot,
- Strategy&Input:Prompt: "Here is my `tools.py`. Generate 3 test cases in `tests/test_tools.py` that trigger the failure modes I defined (e.g., empty wardrobe, impossible search).
."
- Verification: Execute `pytest` and ensure the agent returns the expected user-friendly error string instead of crashing.
*
**Milestone 6 — Documentation:*
AI Tool: Gemini/copilot,
- Strategy&Input:Prompt: Prompt: "Write a professional README.md for this agent. Include the tool inventory, explain the planning loop logic, and summarize my AI usage (provide the specific instances below)."
."
- Verification:Manually review for tone and ensure the README matches the actual code signatures.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:*Searching for Items *
<!-- What does the agent do first? Which tool is called? With what input? -->
1. The agent parses the user's natural language to extract parameters. It calls `search_listings(description="vintage graphic tee", size="M", max_price=30.0)`. The tools accesses `data/listings.json` using `load_listings()` and returns a list of dictionaries matching these criteria.
**If results are found: The agent stores the top result (the item dictionary) in the session state as selected_item.

**If no results are found: The agent terminates the loop and informs the user: "I couldn't find any graphic tees in that price range and size. Try removing the size filter or increasing your budget."

**Step 2:* Suggesting an Outfit *
<!-- What happens next? What was returned from step 1? What tool is called now? -->
With the selected_item now in the session state, the agent calls      `suggest_outfit(new_item=session['selected_item'], wardrobe=get_example_wardrobe())`. This tool sends the new item and the user's existing wardrobe items to the LLM. The LLM processes the combination and returns a text string containing specific styling advice (e.g., "Pair this with your wide-leg jeans..."). This string is saved to the session state as  `outfit_suggestion`.

**Step 3:* Generating the Fit Card*
<!-- Continue until the full interaction is complete -->
Finally, the agent calls `create_fit_card(outfit=session['outfit_suggestion'], new_item=session['selected_item'])`. This tool takes the styling advice and the item details to generate a short, social-media-ready caption. This final string is saved to the session state as `fit_card`.
**Final output to user:* Response to the user query*
<!-- What does the user actually see at the end? -->
The user sees a response containing the details of the item found, the personalized styling advice, and the final shareable "Fit Card" caption: "Thrifted this faded band tee off Depop for $22 and honestly it was made for my wide-legs 🖤 full look in my stories"