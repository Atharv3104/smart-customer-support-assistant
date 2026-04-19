from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
# import openai  # Uncomment when you add your API key

import json
import os
import datetime
try:
    from fpdf import FPDF
except ImportError:
    pass

# Setup Flask to serve static frontend files automatically
app = Flask(__name__, static_url_path='', static_folder='.')
# Enable CORS so our frontend can communicate with this backend API
CORS(app)

# =====================================================================
# To use REAL OpenAI GPT, uncomment the import above and the code below.
# openai.api_key = "YOUR_OPENAI_API_KEY_HERE"
# =====================================================================

# Backend context memory (session simple fallback)
session_memory = {}

@app.route('/')
def home():
    """Serves the frontend application so you can open localhost:5000 directly!"""
    return send_from_directory('.', 'index.html')

def save_to_database(session_id, user_msg, bot_reply):
    """Saves the conversation to a local JSON file to act as a database log."""
    log_file = 'database_logs.json'
    logs = {}
    
    # Read existing logs if the file exists
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except:
            pass
            
    # Add new interaction into the session's log array
    if session_id not in logs:
        logs[session_id] = []
        
    logs[session_id].append({
        "timestamp": str(datetime.datetime.now()),
        "user_message": user_msg,
        "ai_response": bot_reply
    })
    
    # Write back to file
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=4)
        
    # Also save to PDF on Desktop
    try:
        if 'FPDF' in globals():
            desktop = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'OneDrive', 'Desktop')
            if not os.path.exists(desktop):
                desktop = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Desktop')
                
            pdf_file = os.path.join(desktop, f"Chat_History_{session_id}.pdf")
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Nexus Smart Support - Chat History", ln=True, align='C')
            pdf.ln(10)
            
            for entry in logs[session_id]:
                t = entry.get('timestamp', '')[:19]
                u_msg = entry.get('user_message', '')
                a_msg = entry.get('ai_response', '').replace('<br>', '\n').replace('<b>', '').replace('</b>', '').replace('**', '')
                
                # Basic encoding for FPDF default font
                u_msg = u_msg.encode('latin-1', 'replace').decode('latin-1')
                a_msg = a_msg.encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font("Arial", 'B', 12)
                pdf.multi_cell(0, 10, txt=f"User [{t}]:\n{u_msg}")
                pdf.set_font("Arial", '', 12)
                pdf.multi_cell(0, 10, txt=f"Nexus [{t}]:\n{a_msg}")
                pdf.ln(5)
                
            pdf.output(pdf_file)
    except Exception as e:
        print("Error saving PDF:", e)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main API endpoint for the Nexus Support Assistant.
    Expects JSON: { "session_id": "123", "message": "Where is my order?", "history": [...] }
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    session_id = data.get('session_id', 'default_user')
    user_message = data.get('message', '').lower()
    
    # 1. Maintain conversation history/context provided by the frontend
    history = data.get('history', [])
    
    # Enable this block if using OpenAI
    """
    try:
        messages = [{"role": "system", "content": "You are Nexus, a helpful e-commerce support AI... do not lie."}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        bot_reply = response.choices[0].message.content
        return jsonify({"reply": bot_reply})
        
    except Exception as e:
        return jsonify({"reply": f"OpenAI Error: {str(e)}"}), 500
    """

    # 2. Mock API Fallback with Context Engine
    # If we are waiting for an order ID
    state = session_memory.get(session_id, {"waiting_for_order": False, "escalated": False})
    
    if 'reset' in user_message or 'end' in user_message or 'restart' in user_message:
        session_memory[session_id] = {"waiting_for_order": False, "escalated": False}
        response_data = {"reply": "Chat reset. You are now speaking with Nexus AI again. How can I assist you?", "buttons": []}
        save_to_database(session_id, user_message, response_data["reply"])
        return jsonify(response_data)

    if state["escalated"]:
        # Dynamic mock human responses
        if 'faq' in user_message or 'question' in user_message:
            state["escalated"] = False
            session_memory[session_id] = state
            response_data = {
                "reply": "Switching back to Nexus AI. Here are some of our most frequently asked questions:",
                "buttons": [
                    {'text': 'How do I return an item?', 'action': 'faqReturn'},
                    {'text': 'Do you ship internationally?', 'action': 'faqShip'}
                ]
            }
        else:
            if user_message.strip().isdigit() and 1 <= int(user_message.strip()) <= 20:
                answers = {
                    1: "1. The product details include specifications such as size, material, features, and usage instructions, which are available on the product page.",
                    2: "2. Available sizes and colors are listed on the product page. You can select your preferred option before placing the order.",
                    3: "3. All products are genuine and may include a manufacturer warranty if specified in the product details.",
                    4: "4. The product price is displayed on the product page and includes applicable taxes. Any additional charges will be shown at checkout.",
                    5: "5. Stock availability is updated on the product page. If unavailable, the product will be marked as “Out of Stock.”",
                    6: "6. Orders are typically delivered within 3–7 business days, depending on location and availability.",
                    7: "7. Delivery charges, if applicable, are displayed at checkout before completing the payment.",
                    8: "8. Once the order is shipped, a tracking link will be shared via SMS or email for real-time tracking.",
                    9: "9. Multiple payment options are available, including Debit/Credit Cards, UPI, Net Banking, and Cash on Delivery (if applicable).",
                    10: "10. All online transactions are secured with encryption to ensure safe and reliable payments.",
                    11: "11. Orders can be canceled before they are shipped through the user account or by contacting customer support.",
                    12: "12. Refund requests can be submitted through the user account or by contacting customer support with order details.",
                    13: "13. Refunds are generally processed within 5–10 business days after approval.",
                    14: "14. The refund amount will be credited to the original payment method used during the purchase.",
                    15: "15. Returns are accepted within the specified return period if the product is unused and in its original condition.",
                    16: "16. In case of a damaged or incorrect product, customer support should be contacted immediately with relevant details and proof for resolution.",
                    17: "17. Customer support can be contacted via email, phone, or through the help section of the app or website.",
                    18: "18. Any available discounts or offers are displayed on the product page or during checkout.",
                    19: "19. The delivery address can be updated before the order is shipped by contacting customer support.",
                    20: "20. If delivery is missed, the courier service will attempt redelivery or contact the user to reschedule the delivery."
                }
                agent_msg = "Agent Sarah: " + answers[int(user_message.strip())]
            elif 'solve' in user_message or 'fix' in user_message or 'help' in user_message:
                agent_msg = "Agent Sarah: I have successfully accessed your account and resolved the problem for you! A confirmation email has been sent. Is there anything else I can do?"
            elif len(user_message) < 5:
                agent_msg = "Agent Sarah: Could you please provide more details so I can assist you correctly?"
            elif '?' in user_message:
                agent_msg = "Agent Sarah: That's a great question. Let me verify that with our specialized department right now."
            else:
                agent_msg = f"Agent Sarah: I have looked into your query about '{user_message[:15]}...'. I have instantly resolved this issue for you! Let me know if you need anything else."
                
            response_data = {
                "reply": agent_msg, 
                "buttons": [{'text': 'End Human Chat (Reset)', 'action': 'reset'}]
            }

    elif state["waiting_for_order"]:
        if any(char.isdigit() for char in user_message):
            state["waiting_for_order"] = False
            session_memory[session_id] = state
            response_data = {
                "reply": f"I found your order ID {user_message}. Your order for **Sony Noise-Cancelling Headphones ($149.99)** is currently **Out for Delivery** and should arrive by 8 PM today.",
                "buttons": [{'text': 'Need more help', 'action': 'reset'}]
            }
        else:
            response_data = {"reply": "That doesn't look like a valid numeric Order ID. **Please simply type your tracking number into the text box below and click send.**"}

    # Mock NLP Intent Matching Engine
    elif 'order' in user_message or 'track' in user_message or 'status' in user_message:
        state["waiting_for_order"] = True
        session_memory[session_id] = state
        response_data = {"reply": "I can definitely help you track your order! **Please type your Order ID into the chat box below and hit send (e.g., 12345)**."}
        
    elif 'refund policy' in user_message:
        policy_text = (
            "Thank you for using our service. Please read our refund policy carefully.<br>"
            "1.Refunds are only applicable in cases of duplicate payment, incorrect amount paid, or technical errors.<br>"
            "2.Refund requests must be submitted within 7 working days of the transaction.<br>"
            "3.Once approved, the refund will be processed within 5–10 business days to the original payment method.<br>"
            "4.No refunds will be issued for successfully completed services unless there is a valid issue."
        )
        response_data = {
            "reply": policy_text
        }
        
    elif 'refund' in user_message or 'payment' in user_message or 'money' in user_message:
        response_data = {
            "reply": "Your refund will be processed shortly and the amount will be credited back to the original payment method used during the purchase.",
            "buttons": [{'text': 'View refund policy', 'action': 'refundPolicy'}]
        }
        
    elif 'faq' in user_message or 'question' in user_message or 'help' in user_message:
        response_data = {
            "reply": "Here are some of our most frequently asked questions:",
            "buttons": [
                {'text': 'How do I return an item?', 'action': 'faqReturn'},
                {'text': 'Do you ship internationally?', 'action': 'faqShip'}
            ]
        }
        
    elif 'return' in user_message:
        response_data = {"reply": "You can return most items within 30 days of receipt. Please visit our returns page to print a prepaid shipping label."}
        
    elif 'ship internationally' in user_message or 'internationally' in user_message or 'ship' in user_message:
        response_data = {"reply": "Yes, we ship internationally! International shipping typically takes 7-14 business days, and additional customs fees may apply."}
        
    elif 'human' in user_message or 'agent' in user_message or 'speak' in user_message:
        state["escalated"] = True
        session_memory[session_id] = state
        questions_list = (
            "I'm escalating your chat to Agent Sarah. Meanwhile, here are some questions she can answer for you:<br><br>"
            "1. What are the details of this product?<br>"
            "2. Is this product available in different sizes or colors?<br>"
            "3. Is the product original and does it have a warranty?<br>"
            "4. What is the price of the product?<br>"
            "5. Is this product currently in stock?<br>"
            "6. When will my order be delivered?<br>"
            "7. What are the delivery charges?<br>"
            "8. Can I track my order?<br>"
            "9. What payment methods are available?<br>"
            "10. Is online payment safe?<br>"
            "11. Can I cancel my order after placing it?<br>"
            "12. How can I request a refund?<br>"
            "13. How long does it take to receive a refund?<br>"
            "14. Will the refund be sent to my original payment method?<br>"
            "15. Can I return the product if I don’t like it?<br>"
            "16. What should I do if I receive a damaged or wrong product?<br>"
            "17. How can I contact customer support?<br>"
            "18. Are there any discounts or offers available?<br>"
            "19. Can I change my delivery address after placing the order?<br>"
            "20. What happens if I miss the delivery?<br><br>"
            "**Please enter the question number to get an instant answer!**"
        )
        response_data = {"reply": questions_list, "action": "escalate"}
        
    elif 'hello' in user_message or 'hi' in user_message:
        response_data = {"reply": "Hello there! I'm Nexus. How can I help you today?"}
         
    else:
        response_data = {
            "reply": "I'm not quite sure I understand. Could you rephrase that? Or I can escalate you to a human agent.",
            "buttons": [{'text': 'Connect to Human Agent', 'action': 'escalate'}]
        }

    # Save to our JSON file database!
    save_to_database(session_id, user_message, response_data["reply"])
    
    return jsonify(response_data)

if __name__ == '__main__':
    # Runs the backend server locally on port 5000
    print("Nexus Backend API is running on http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
