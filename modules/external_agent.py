import json
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from modules.helpers import print_lg
from modules.ai.openaiConnections import ai_completion

def extract_form_schema(driver: WebDriver) -> str:
    """
    Extracts a simplified JSON representation of the form fields on the current page.
    This reduces token count for the LLM.
    """
    js_script = """
    let fields = [];
    let inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(el => {
        // Skip hidden or irrelevant fields
        if (el.type === 'hidden' || el.style.display === 'none' || el.disabled) return;
        
        let label = '';
        if (el.id) {
            let labelEl = document.querySelector(`label[for="${el.id}"]`);
            if (labelEl) label = labelEl.innerText.trim();
        }
        if (!label) label = el.getAttribute('aria-label') || el.name || el.placeholder || 'Unknown';
        
        let options = [];
        if (el.tagName.toLowerCase() === 'select') {
            el.querySelectorAll('option').forEach(opt => {
                options.push({value: opt.value, text: opt.innerText.trim()});
            });
        }
        
        // Generate a unique CSS selector for this element
        let selector = el.id ? `#${el.id}` : (el.name ? `[name="${el.name}"]` : '');
        if (!selector) {
            // fallback generic selector (fragile, but works for simple forms)
            selector = el.tagName.toLowerCase();
            if (el.className) selector += `.${el.className.split(' ').join('.')}`;
        }
        
        fields.push({
            tag: el.tagName.toLowerCase(),
            type: el.type,
            name: el.name,
            label: label,
            selector: selector,
            options: options.length > 0 ? options : undefined
        });
    });
    return JSON.stringify(fields);
    """
    try:
        schema = driver.execute_script(js_script)
        return schema
    except Exception as e:
        print_lg("Failed to extract form schema: ", e)
        return "[]"

def ask_llm_to_map_fields(client, form_schema: str, cv_data: str) -> dict:
    """
    Sends the form schema and CV data to the LLM to get a mapping.
    """
    prompt = f"""
You are an intelligent web form filler. You are given a JSON schema of input fields from a job application website, and the user's CV information.
Your task is to map the user's information to the appropriate form fields.

CV Information:
{cv_data}

Form Schema:
{form_schema}

Return a valid JSON array of objects. Each object must have:
- "selector": The CSS selector of the field (use the exact selector provided in the schema).
- "action": "type" (for text inputs/textareas), "select" (for dropdowns), or "click" (for checkboxes/radios).
- "value": The string value to type or the option value to select.

Example Output:
[
  {{"selector": "#first_name", "action": "type", "value": "John"}},
  {{"selector": "[name='experience_years']", "action": "select", "value": "5-7"}}
]

Only return the JSON array. Do not include markdown formatting or explanations.
"""
    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = ai_completion(client, messages, response_format={"type": "json_object"})
        # Parse the JSON response
        if isinstance(response, str):
            # Try to strip markdown if it snuck in
            if response.startswith("```json"):
                response = response[7:-3].strip()
            return json.loads(response)
        return response
    except Exception as e:
        print_lg("Error mapping fields with LLM:", e)
        return []

def inject_llm_answers(driver: WebDriver, mapping: list):
    """
    Executes the JSON mapping on the page via JavaScript.
    """
    print_lg(f"Injecting {len(mapping)} answers into the form...")
    
    js_injection = """
    const mappings = arguments[0];
    let results = [];
    mappings.forEach(map => {
        try {
            let el = document.querySelector(map.selector);
            if (!el) {
                results.push(`Element not found: ${map.selector}`);
                return;
            }
            if (map.action === 'type') {
                el.value = map.value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            } else if (map.action === 'select') {
                el.value = map.value;
                el.dispatchEvent(new Event('change', { bubbles: true }));
            } else if (map.action === 'click') {
                el.click();
            }
            results.push(`Success: ${map.selector}`);
        } catch (e) {
            results.push(`Error on ${map.selector}: ${e.message}`);
        }
    });
    return results;
    """
    try:
        results = driver.execute_script(js_injection, mapping)
        for res in results:
            print_lg("Injection Result: " + str(res))
    except Exception as e:
        print_lg("Failed to execute injection script:", e)

def process_external_application(driver: WebDriver, client, cv_data: str):
    """
    Main function to handle external ATS processing.
    """
    print_lg("--- Starting Universal External ATS Agent ---")
    time.sleep(3) # Wait for external page to load fully
    
    schema = extract_form_schema(driver)
    if schema == "[]" or not schema:
        print_lg("Could not extract any form fields. The page might be protected or not fully loaded.")
        return False
        
    print_lg(f"Extracted {len(json.loads(schema))} form fields.")
    
    mapping = ask_llm_to_map_fields(client, schema, cv_data)
    
    if mapping and isinstance(mapping, list):
        inject_llm_answers(driver, mapping)
        return True
    else:
        print_lg("LLM did not return a valid mapping.")
        return False
