# Model Armor Integration: Floor Settings vs. Templates

When integrating Model Armor with Vertex AI, you have two primary options for enforcing security and safety policies: **Project-wide Floor Settings** and **Per-request Templates**.

---

## At a Glance Comparison

| Feature          | Floor Settings                  | Templates                                 |
| :--------------- | :------------------------------ | :---------------------------------------- |
| **Scope**        | Project-wide (All Gemini calls) | Per-request (Specific calls)              |
| **Code Changes** | **None**                        | Required (Update `GenerateContentConfig`) |
| **Granularity**  | Coarse (Same for everything)    | Fine (Custom filters per agent)           |
| **Precedence**   | Low (Baseline protection)       | High (Overrides Floor Settings)           |
| **Automation**   | Managed via Terraform/gcloud    | Managed via Terraform + Code              |

---

## 1. Project-wide Floor Settings (Baseline Protection)

Floor settings define the **minimum security standard** for a Google Cloud project. Once enabled, every call to a Gemini model in that project is automatically filtered by Model Armor.

### How it works:

- You enable the Model Armor API.
- You configure the "Floor Setting" resource for the project using `gcloud` or the API.
- Vertex AI automatically routes traffic through this filter before it reaches the model (and before the response reaches your app).

### ✅ Pros:

- **Zero Code Changes**: You don't need to modify your ADK agent or application logic.
- **Uniform Security**: Ensures that even "forgotten" or "shadow" AI implementations in the project are protected.
- **Simpler Life-cycle**: Managed entirely at the infrastructure level.

### ❌ Cons:

- **Single Policy**: You cannot easily have different rules for different agents (e.g., a "strict" HR agent vs. a "flexible" creative writing agent).

---

## 2. Per-request Templates (Granular Control)

Templates are specific configurations that you define and then reference explicitly in your API requests.

### How it works:

- You create one or more named templates (e.g., `projects/.../templates/strict-pii-filter`).
- In your code (e.g., `agent.py`), you pass the template name in the `model_armor_config` field of your request.

### ✅ Pros:

- **Explicit Control**: You can apply different security levels to different user cohorts or agent types.
- **Higher Precedence**: If a request uses a template, it overrides the Floor Settings for that call.
- **Environment Specific**: You can easily swap templates between staging and production via environment variables.

### ❌ Cons:

- **Code Burden**: Requires developers to actively integrate the configuration.
- **Managed Complexity**: You have to track and maintain multiple template IDs.

---

## Recommendation

- **Use Floor Settings if**: You want immediate, project-wide protection with the least amount of effort and don't expect needing different security policies for different agents.
- **Use Templates if**: You are building a complex multi-agent system where different agents handle different types of sensitive data and require tailored filtering rules.

---

> [!IMPORTANT]
> **Precedence Note**: If both are active, the **Template** provided in the API request takes priority. If no template is provided, the **Floor Setting** is applied as the fallback.
