import streamlit as st
import google.generativeai as genai
import re
import time

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
st.set_page_config(page_title="MM Channel AI Subtitles", page_icon="🎬", layout="wide")

st.title("🎬 MM Channel AI Subtitles")
st.markdown("**Advanced Multilingual to Spoken Burmese Subtitle Localization Studio**")

# ==========================================
# 2. Session State Initialization
# ==========================================
if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""
if "is_translating" not in st.session_state:
    st.session_state.is_translating = False
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

# ==========================================
# 3. Sidebar (Settings & API)
# ==========================================
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Enter Google Gemini API Key:", type="password")
    
        model_name = st.selectbox(
        "Select AI Model:",
        [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3.1-pro-preview",
            "gemini-2.5-pro"
        ],
        index=0,
        help="Pro models are recommended for deep reasoning. Flash models are for fast translation."
    )
    
    st.markdown("---")
    st.markdown("""
    **Active Rules:**
    - ✅ Dynamic Context Adaptation
    - ✅ 100% Spoken Burmese
    - ✅ Zero Punctuation (No ။, ၊, ?, !)
    - ✅ Auto Brackets (...) [...] Cleaning
    - ✅ Universal 2-Speaker Split
    - ✅ Hidden Output Until Completed
    """)

# ==========================================
# 4. System Prompt & Rules
# ==========================================
SYSTEM_PROMPT = """
Role: You are "MM Channel AI Subtitles", an advanced multilingual Burmese Subtitle Localization & AI Expert.

1. MULTILINGUAL TRANSLATION SUPPORT:
Accurately translate dialogue from Japanese, Korean, English, Chinese, Thai, and other source languages directly into natural spoken Burmese.

2. DYNAMIC GENRE ADAPTATION (No Presets):
Automatically adapt the translation tone, style, and terminology based on the context of the movie or show without relying on fixed presets.

3. AUTOMATIC CLEANING & FILTERING RULES:
- Parentheses Cleaning (...): Automatically detect and remove any text enclosed in normal brackets (...).
- Brackets Cleaning [...]: Automatically detect and remove any sound effects or vocal descriptions enclosed in square brackets [...].
- No Interjections / Filler Sounds: Exclude unnecessary vocal noises and fillers (အဟမ်း, ဟား, ဟေး, အား).

4. STRICT SUBTITLE TRANSLATION & FORMATTING RULES:
- 100% Spoken Burmese: Use natural conversational movie Burmese (ရုပ်ရှင်စကားပြောဟန်). Avoid formal or literary particles (သည်, ၏, ၌, ၎င်း).
- Zero Punctuation: NEVER include punctuation marks (။, ၊, ?, !) in any subtitle line. Use spaces and question particles (လား, လဲ, တုန်း, ဟင်).
- Universal 2-Speaker Split: Automatically split long sentences and two-speaker dialogues into balanced separate lines within the same timestamp block.
- Format Preservation: Strictly preserve .srt timestamps (00:00:00,000 --> 00:00:00,000). Never merge or split timestamp blocks. Return ONLY the translated SRT format.
"""

# ==========================================
# 5. Helper Functions
# ==========================================
def chunk_srt(srt_content, chunk_size=20):
    """Splits SRT content into manageable chunks to avoid AI token limits."""
    blocks = srt_content.strip().split('\n\n')
    return [blocks[i:i + chunk_size] for i in range(0, len(blocks), chunk_size)]

def stop_translation():
    """Trigger the stop process."""
    st.session_state.stop_requested = True

# ==========================================
# 6. Main UI & Processing
# ==========================================
uploaded_file = st.file_uploader("📂 Upload .SRT or .ASS File", type=['srt', 'ass'])

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    st.success(f"File '{uploaded_file.name}' loaded successfully!")
    
    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("✨ Translate to Spoken Burmese", type="primary", use_container_width=True)
    with col2:
        stop_btn = st.button("🛑 Stop Translation", on_click=stop_translation, use_container_width=True)

    if start_btn:
        if not api_key:
            st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)
            
            st.session_state.is_translating = True
            st.session_state.stop_requested = False
            st.session_state.translated_text = ""
            
            # Placeholder for "Hidden Until Translated" rule
            status_box = st.info("⏳ ဘာသာပြန်ရန် စောင့်ဆိုင်းနေပါသည်... (Output is Hidden Until Translated)")
            progress_bar = st.progress(0)
            
            # Processing in Chunks
            chunks = chunk_srt(file_content, chunk_size=25)
            total_chunks = len(chunks)
            final_output = ""
            
            try:
                for idx, chunk in enumerate(chunks):
                    # Check for Stop Command
                    if st.session_state.stop_requested:
                        status_box.warning("🛑 ဘာသာပြန်ခြင်းကို ရပ်တန့်လိုက်ပါပြီ (Translation Stopped). Progress saved.")
                        break
                    
                    chunk_text = "\n\n".join(chunk)
                    prompt = f"Translate the following subtitle blocks into Spoken Burmese maintaining the exact SRT format:\n\n{chunk_text}"
                    
                    # Call Gemini API
                    response = model.generate_content(prompt)
                    final_output += response.text.strip() + "\n\n"
                    
                    # Update Progress
                    progress = (idx + 1) / total_chunks
                    progress_bar.progress(progress)
                    
                    # Small delay to avoid API rate limits
                    time.sleep(2)
                
                st.session_state.translated_text = final_output
                st.session_state.is_translating = False
                
                if not st.session_state.stop_requested:
                    status_box.success("✅ ဘာသာပြန်ခြင်း အောင်မြင်စွာ ပြီးဆုံးပါပြီ။")
                    progress_bar.empty()
                    
            except Exception as e:
                st.error(f"❌ Error occurred: {e}")
                st.session_state.is_translating = False

# ==========================================
# 7. Output Area (Strict Display Control)
# ==========================================
if st.session_state.translated_text and not st.session_state.is_translating:
    st.markdown("### 🎉 Translated Subtitles")
    
    # Download Button
    st.download_button(
        label="📥 Export Translated Subtitles (.srt)",
        data=st.session_state.translated_text,
        file_name=f"MM_Translated_{uploaded_file.name if uploaded_file else 'output.srt'}",
        mime="text/plain",
        type="primary"
    )
    
    # Text Area for Review
    st.text_area("Review Subtitles:", st.session_state.translated_text, height=400)
