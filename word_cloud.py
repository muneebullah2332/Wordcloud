import streamlit as st 
import pandas as pd 
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from docx import Document
from pypdf import PdfReader
import base64
from io import BytesIO
import csv

# functions for file reading
def read_text(file):
    return file.getvalue().decode('utf-8')

def read_doc(file):
    doc = Document(file)
    return ' '.join([paragraph.text for paragraph in doc.paragraphs])

def read_pdf(file):
    pdf_reader = PdfReader(file)
    text = []
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:  # Only add if text exists
            text.append(page_text)
    return ' '.join(text)

def read_csv(file):
    # Try reading with different encodings if needed
    try:
        df = pd.read_csv(file)
        # Combine all text columns
        text_columns = df.select_dtypes(include=['object']).columns
        return ' '.join(df[col].astype(str).str.cat(sep=' ') for col in text_columns)
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        return ""

# function to filter out stopwords
def filter_stopwords(text, additional_stopwords=[]):
    words = text.split()
    allstopwords = STOPWORDS.union(set(additional_stopwords))
    filtered_words = [word for word in words if word.lower() not in allstopwords]
    return ' '.join(filtered_words)

# function to create the download link for plot
def get_plot_download_link(plot, filename):
    buf = BytesIO()
    plot.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    plot_data = base64.b64encode(buf.read()).decode("utf-8")
    href = f'<a href="data:file/png;base64,{plot_data}" download="{filename}">Download Plot</a>'
    return href

# function to generate a download link for a dataframe
def get_df_download_link(df, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    return href
    
# streamlit code
st.title("📊 Word Cloud Generator")
st.write("Generate word clouds from text files, Word documents, PDFs, or CSV files")

# File upload
uploaded_file = st.file_uploader("Choose a file", 
                               type=['txt', 'docx', 'pdf', 'csv'],
                               help="Upload a text-based file to generate a word cloud")

# Additional options
st.sidebar.header("Customization Options")
max_words = st.sidebar.slider("Max number of words", 50, 500, 200)
background_color = st.sidebar.color_picker("Background color", "#ffffff")
colormap = st.sidebar.selectbox("Color scheme", 
                               ["viridis", "plasma", "inferno", "magma", "cividis", "rainbow"])
contour_width = st.sidebar.slider("Word border width", 0, 10, 0)
contour_color = st.sidebar.color_picker("Word border color", "#000000")

# Custom stopwords
st.sidebar.header("Stopword Settings")
custom_stopwords = st.sidebar.text_area("Add custom stopwords (comma separated)", "",
                                      help="Words you want to exclude from the word cloud")
additional_stopwords = [word.strip() for word in custom_stopwords.split(",")] if custom_stopwords else []

if uploaded_file:
    # Read file based on type
    file_type = uploaded_file.type
    if file_type == "text/plain":
        text = read_text(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = read_doc(uploaded_file)
    elif file_type == "application/pdf":
        text = read_pdf(uploaded_file)
    elif file_type == "text/csv" or uploaded_file.name.endswith('.csv'):
        text = read_csv(uploaded_file)
    else:
        st.error("Unsupported file type")
        st.stop()
    
    if not text.strip():
        st.error("The uploaded file appears to be empty or couldn't be read properly.")
    else:
        # Show text preview
        with st.expander("Preview extracted text"):
            st.text(text[:1000] + ("..." if len(text) > 1000 else ""))
        
        # Filter stopwords
        filtered_text = filter_stopwords(text, additional_stopwords)
        
        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400, 
                            background_color=background_color,
                            max_words=max_words,
                            colormap=colormap,
                            contour_width=contour_width,
                            contour_color=contour_color).generate(filtered_text)
        
        # Display word cloud
        st.subheader("Generated Word Cloud")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        
        # Download options
        st.markdown(get_plot_download_link(fig, "wordcloud.png"), unsafe_allow_html=True)
        
        # Show word frequencies
        st.subheader("Word Frequency Analysis")
        word_freq = wordcloud.words_
        freq_df = pd.DataFrame(list(word_freq.items()), columns=['Word', 'Frequency'])
        freq_df = freq_df.sort_values('Frequency', ascending=False)
        
        # Display top words
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(freq_df.head(20))
        with col2:
            st.bar_chart(freq_df.head(10).set_index('Word'))
        
        st.markdown(get_df_download_link(freq_df, "word_frequencies.csv"), unsafe_allow_html=True)