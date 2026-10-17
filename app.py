import streamlit as st
import google.generativeai as genai
import re
import time

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
st.set_page_config(page_title="MM Channel AI Subtitles", page_icon="🎬")

st.title("🎬 MM Channel AI Subtitles")
st.markdown("***Advanced Multilingual to Spoken Burmese Subtitle Localization Studio***")

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
Role: You are "MM Channel AI Subtitles", an advanced multilingual Burmese Subtitle Translator.

1. MULTILINGUAL TRANSLATION SUPPORT:
Accurately translate dialogue from Japanese, Korean, English, Chinese, Thai, etc. into Burmese.

2. DYNAMIC GENRE ADAPTATION (No Presets):
Automatically adapt the translation tone, style, and terminology based on the context of the dialogue.

3. AUTOMATIC CLEANING & FILTERING RULES:
- Parentheses Cleaning (...): Automatically detect and remove any text enclosed in parentheses.
- Brackets Cleaning [...]: Automatically detect and remove any sound effects or cues.
- No Interjections / Filler Sounds: Exclude unnecessary vocal noises.

4. STRICT SUBTITLE TRANSLATION & FORMATTING RULES:
- 100% Spoken Burmese: Use natural conversational movie Burmese (ပြောစကားပုံစံ).
- Zero Punctuation: NEVER include punctuation marks (။, ၊, ?, !) in any subtitle line.
- Universal 2-Speaker Split: Automatically split long sentences for two speakers appropriately.
- Format Preservation: Strictly preserve .srt or .ass timestamps.
"""

# ==========================================
# 5. Helper Functions
# ==========================================
def chunk_srt(srt_content, chunk_size=20):
    blocks = srt_content.strip().split('\n\n')
    return [blocks[i:i + chunk_size] for i in range(0, len(blocks), chunk_size)]

def stop_translation():
    st.session_state.stop_requested = True

# ==========================================
# 6. Main App UI & Logic
# ==========================================
uploaded_file = st.file_uploader("📂 Upload .SRT or .ASS File", type=["srt", "ass"])

if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Translation", use_container_width=True, disabled=st.session_state.is_translating):
            if not api_key:
                st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
            else:
                st.session_state.is_translating = True
                st.session_state.stop_requested = False
                st.session_state.translated_text = ""
                st.rerun()
                
    with col2:
        if st.button("🛑 Stop", use_container_width=True, on_click=stop_translation, disabled=not st.session_state.is_translating):
            pass

    # Translation Logic
    if st.session_state.is_translating:
        st.info("⏳ Translation in progress... Output is hidden until completed.")
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name=model_name, system_instruction=SYSTEM_PROMPT)
            
            chunks = chunk_srt(file_content)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            final_output = []
            
            for i, chunk in enumerate(chunks):
                if st.session_state.stop_requested:
                    st.warning("🛑 Translation stopped by user.")
                    break
                    
                chunk_text = "\n\n".join(chunk)
                status_text.text(f"Translating chunk {i+1} of {len(chunks)}...")
                
                # Gemini API Call
                response = model.generate_content(chunk_text)
                final_output.append(response.text)
                
                progress_bar.progress((i + 1) / len(chunks))
                time.sleep(1) # Rate limit protection
                
            if not st.session_state.stop_requested:
                st.session_state.translated_text = "\n\n".join(final_output)
                st.success("✅ Translation Completed!")
                
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
            
        finally:
            st.session_state.is_translating = False
            st.rerun()

# ==========================================
# 7. Final Output Display & Download
# ==========================================
if st.session_state.translated_text:
    st.subheader("🎉 Translated Subtitles")
    st.text_area("Result", st.session_state.translated_text, height=300)
    
    file_extension = uploaded_file.name.split('.')[-1]
    new_filename = uploaded_file.name.replace(f".{file_extension}", f"_MM.{file_extension}")
    
    st.download_button(
        label="💾 Download Translated File",
        data=st.session_state.translated_text,
        file_name=new_filename,
        mime="text/plain",
        use_container_width=True
    )
