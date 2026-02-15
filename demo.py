
import json
import os
import tempfile

import pandas as pd
import streamlit as st

from engine.analyzer import run_analysis

st.set_page_config(page_title="Communication Forensic Tool", page_icon="🕵️‍♀️", layout="wide")

st.title("🕵️‍♀️ Communication Forensic Tool")
st.markdown("""
**Research-informed pattern detection for text analysis.**
*100% Local Privacy. No data leaves your machine.*
""")

uploaded_file = st.file_uploader("Upload SMS Backup XML", type=["xml"])

if uploaded_file:
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded file
        source_path = os.path.join(temp_dir, "sms_backup.xml")
        with open(source_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Setup output config
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        config = {
            "case_name": "Demo Case",
            "user_label": "User",
            "contact_label": "Contact",
            "sms_xml": source_path,
            "output_dir": output_dir,
            "phone_suffix": ""
        }

        config_path = os.path.join(temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        with st.spinner("Analyzing patterns... (DARVO, Generic, Positive)"):
            try:
                # Run the actual engine
                # Note: run_analysis is designed to be CLI-driven, so we might need to adapt it
                # For this demo, we assume run_analysis writes files to output_dir
                run_analysis(config_path=config_path, use_db=False)

                st.success("Analysis Complete!")

                # Load Results
                data_path = os.path.join(output_dir, "DATA.json")
                if os.path.exists(data_path):
                    with open(data_path) as f:
                        data = json.load(f)

                    # Display Stats
                    col1, col2, col3 = st.columns(3)
                    start = data.get("period", {}).get("start", "N/A")
                    end = data.get("period", {}).get("end", "N/A")

                    # Calculate totals
                    total_msgs = 0
                    patterns_found = 0
                    for _, stats in data.get("days", {}).items():
                        total_msgs += stats.get("messages_sent", 0) + stats.get("messages_received", 0)
                        patterns_found += len(stats.get("hurtful_from_contact", [])) + len(stats.get("patterns_from_contact", []))

                    col1.metric("Total Messages", total_msgs)
                    col2.metric("timeline", f"{start} to {end}")
                    col3.metric("Flags Detected", patterns_found)

                    st.divider()

                    # Mock timeline view
                    st.subheader("🚩 Flagged Incidents (Preview)")

                    # Collect all flagged messages
                    flags = []
                    for day, stats in data.get("days", {}).items():
                        for p in stats.get("patterns_from_contact", []):
                            flags.append({
                                "Date": day,
                                "Pattern": p.get("pattern"),
                                "Severity": p.get("severity"),
                                "Message": p.get("message")
                            })

                    if flags:
                        df = pd.DataFrame(flags)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No high-conflict patterns detected in this sample.")

                else:
                    st.error("Analysis finished but no data found.")

            except Exception as e:
                st.error(f"Error during analysis: {e!s}")
