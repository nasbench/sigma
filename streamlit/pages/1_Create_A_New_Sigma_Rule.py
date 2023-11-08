# Author(s): Michael Haag (@M_haggis) & Nasreddine Bencherchali (@nas_bench)
# Version: 10-23

from datetime import datetime
from PIL import Image
import json
import openai
import streamlit as st
import uuid
import uuid
import yaml
import base64
from urllib.parse import quote_plus
from streamlit_ace import st_ace, KEYBINDINGS, LANGUAGES, THEMES


def sigma_title_desc(openai_api_key, sigma_rule_logic):
    # Author: Harrison Van Riper (@pseudohvr)
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role": "system",
                "content": "You are a cybersecurity tool designed to create titles and descriptions for Sigma detection rules. The following Sigma rule examples show the correlation between the detection logic and the title and description.\n\nSigma rule examples:\n---\ntitle: File Encoded To Base64 Via Certutil.EXE\ndescription: Detects the execution of certutil with the \"encode\" flag to encode a file to base64. This can be abused by threat actors and attackers for data exfiltration\nlogsource:\n    category: process_creation\n    product: windows\ndetection:\n    selection_img:\n        - Image|endswith: '\\certutil.exe'\n        - OriginalFileName: 'CertUtil.exe'\n    selection_cli:\n        CommandLine|contains:\n            - '-encode'\n            - '/encode'\n    condition: all of selection_*\n---\ntitle: Greedy File Deletion Using Del\ndescription: Detects execution of the \"del\" builtin command to remove files using greedy/wildcard expression. This is often used by malware to delete content of folders that perhaps contains the initial malware infection or to delete evidence.\nlogsource:\n    category: process_creation\n    product: windows\ndetection:\n    # Example:\n    #   del C:\\ProgramData\\*.dll & exit\n    selection_img:\n        - Image|endswith: '\\cmd.exe'\n        - OriginalFileName: 'Cmd.Exe'\n    selection_del:\n        CommandLine|contains:\n            - 'del '\n            - 'erase '\n    selection_extensions:\n        CommandLine|contains:\n            - '\\\\\\*.au3'\n            - '\\\\\\*.dll'\n            - '\\\\\\*.exe'\n            - '\\\\\\*.js'\n    condition: all of selection_*\n---\ntitle: NtdllPipe Like Activity Execution\ndescription: Detects command that type the content of ntdll.dll to a different file or a pipe in order to evade AV / EDR detection. As seen being used in the POC NtdllPipe\nlogsource:\n    category: process_creation\n    product: windows\ndetection:\n    selection:\n        CommandLine|contains:\n            - 'type %windir%\\system32\\ntdll.dll'\n            - 'type %systemroot%\\system32\\ntdll.dll'\n            - 'type c:\\windows\\system32\\ntdll.dll'\n            - '\\\\ntdll.dll > \\\\\\\\.\\\\pipe\\\\'\n    condition: selection\n---\ntitle: Unusual Parent Process For Cmd.EXE\ndescription: Detects suspicious parent process for cmd.exe\nlogsource:\n    category: process_creation\n    product: windows\ndetection:\n    selection:\n        Image|endswith: '\\cmd.exe'\n        ParentImage|endswith:\n            - '\\csrss.exe'\n            - '\\ctfmon.exe'\n            - '\\dllhost.exe'\n            - '\\epad.exe'\n            - '\\FlashPlayerUpdateService.exe'\n            - '\\GoogleUpdate.exe'\n            - '\\jucheck.exe'\n            - '\\jusched.exe'\n            - '\\LogonUI.exe'\n            - '\\lsass.exe'\n            - '\\regsvr32.exe'\n            - '\\SearchIndexer.exe'\n            - '\\SearchProtocolHost.exe'\n            - '\\SIHClient.exe'\n            - '\\sihost.exe'\n            - '\\slui.exe'\n            - '\\spoolsv.exe'\n            - '\\sppsvc.exe'\n            - '\\taskhostw.exe'\n            - '\\unsecapp.exe'\n            - '\\WerFault.exe'\n            - '\\wergmgr.exe'\n            - '\\wlanext.exe'\n            - '\\WUDFHost.exe'\n    condition: selection\n---\ntitle: PUA - Ngrok Execution\ndescription: |\n  Detects the use of Ngrok, a utility used for port forwarding and tunneling, often used by threat actors to make local protected services publicly available.\n  Involved domains are bin.equinox.io for download and *.ngrok.io for connections.\nlogsource:\n    category: process_creation\n    product: windows\ndetection:\n    selection1:\n        CommandLine|contains:\n            - ' tcp 139'\n            - ' tcp 445'\n            - ' tcp 3389'\n            - ' tcp 5985'\n            - ' tcp 5986'\n    selection2:\n        CommandLine|contains|all:\n            - ' start '\n            - '--all'\n            - '--config'\n            - '.yml'\n    selection3:\n        Image|endswith: 'ngrok.exe'\n        CommandLine|contains:\n            - ' tcp '\n            - ' http '\n            - ' authtoken '\n    selection4:\n        CommandLine|contains:\n            - '.exe authtoken '\n            - '.exe start --all'\n    condition: 1 of selection*\n---\ntitle: HackTool - SharpUp PrivEsc Tool Execution\ndescription: Detects the use of SharpUp, a tool for local privilege escalation\nlogsource:\n    category: process_creation\n    product: windows\ndetection:\n    selection:\n        - Image|endswith: '\\SharpUp.exe'\n        - Description: 'SharpUp'\n        - CommandLine|contains:\n              - 'HijackablePaths'\n              - 'UnquotedServicePath'\n              - 'ProcessDLLHijack'\n              - 'ModifiableServiceBinaries'\n              - 'ModifiableScheduledTask'\n              - 'DomainGPPPassword'\n              - 'CachedGPPPassword'\n    condition: selection\n-----",
            },
            {
                "role": "user",
                "content": f"Create a Title and Description for the following Sigma rule. The output should be a JSON dictionary and only contain the title and description.\n\nSigma rule:\n---\ntitle: \ndescription: \n{sigma_rule_logic}",
            },
        ],
        temperature=0.5,
        max_tokens=350,
    )
    sigma_title_desc = json.loads(response["choices"][0]["message"]["content"])

    return sigma_title_desc


def test_title(title):
    errors = []
    allowed_lowercase_words = [
        "the",
        "for",
        "in",
        "with",
        "via",
        "on",
        "to",
        "without",
        "of",
        "through",
        "from",
        "by",
        "as",
        "a",
        "or",
        "at",
        "and",
        "an",
        "over",
        "new",
    ]

    if not title:
        errors.append("Rule has a missing 'title'.")

    if len(title) > 100:
        errors.append("Rule a title field with too many characters (>100)")

    if title.startswith("Detects "):
        errors.append("Rule has a title that starts with 'Detects'")
    if title.endswith("."):
        errors.append("Rule has a title that ends with '.'")

    wrong_casing = []
    for word in title.split(" "):
        if (
            word.islower()
            and not word.lower() in allowed_lowercase_words
            and not "." in word
            and not "/" in word
            and not word[0].isdigit()
        ):
            wrong_casing.append(word)
    if len(wrong_casing) > 0:
        errors.append(
            f"Rule has a title that has not title capitalization. Words: {wrong_casing}"
        )

    return errors


def test_falsepositives(falsepositives):
    errors = []
    banned_words = ["none", "pentest", "penetration test"]
    common_typos = ["unkown", "ligitimate", "legitim ", "legitimeate"]

    if falsepositives:
        for fp in falsepositives:
            # First letter should be capital
            try:
                if fp[0].upper() != fp[0]:
                    errors.append(
                        f"Rule defines a falsepositive item that does not start with a capital letter: {fp}."
                    )
            except TypeError as err:
                errors.append("The rule has an empty falsepositive item")

        for fp in falsepositives:
            for typo in common_typos:
                if fp == "Unknow" or typo in fp.lower():
                    errors.append(
                        f"The Rule defines a falsepositive with a common typo: {fp}."
                    )

            for banned_word in banned_words:
                if banned_word in fp.lower():
                    errors.append(
                        f"The rule defines a falsepositive with an invalid reason: {banned_word}."
                    )

    return errors


# Remove empty values from a nested dict - https://stackoverflow.com/questions/27973988/how-to-remove-all-empty-fields-in-a-nested-dict
# We need this to remove unnecessary logsource
def clean_empty(d):
    if isinstance(d, dict):
        return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if v}
    if isinstance(d, list):
        return [v for v in map(clean_empty, d) if v]
    return d


class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)


st.set_page_config(
    page_title="⚒️ SigmaHQ Rule Creation",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=Image.open("streamlit/favicon.png"),
)
custom_css = """
    <style>
        body {
            background-color: #11252F;
        }
    </style>
    """

with open("streamlit/logsource_data.json", "r") as file:
    logsource_content = json.loads(file.read())

st.markdown(custom_css, unsafe_allow_html=True)
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

if "ai_settings" not in st.session_state:
    st.session_state["ai_settings"] = {
        "api": "",
        "id": "",
        "file": "",
    }

if (
    "content_data_new" not in st.session_state
    or st.session_state["ai_settings"]["file"] != ""
):
    st.session_state["content_data_new"] = {
        "title": "Enter the title of the rule",
        "id": str(uuid.uuid4()),
        "related": [{"id": "", "type": ""}],
        "status": "Select the status of the rule",
        "description": "Enter a description for the rule",
        "references": ["Enter references"],
        "author": "Enter the author name",
        "date": "Enter the date of creation",
        "tags": ["Enter any relevant tags"],
        "logsource": {
            "product": "Enter the product name",
            "service": "Enter the service name",
            "category": "Enter the category name",
        },
        "detection": {
            "selection": {"Image|endswith": "\whoami.exe"},
            "condition": "selection",
        },
        "falsepositives": ["Enter any known false positives"],
        "level": "Select the severity level",
    }
    st.session_state["ai_settings"]["file"] = ""

st.title("⚒️ SigmaHQ Rule Creation")

tab1, tab2, tab3 = st.tabs(["Rule View", "Getting Started", "Logsource Taxonomy"])

with st.sidebar:
    st.title("AI Settings")
    st.session_state["ai_settings"]["api"] = st.text_input(
        "OpenAI API Key",
        st.session_state["ai_settings"]["api"],
        help="You can leverage AI to help generate automatic titles and descriptions. All you need is an OpenAI API key generated from https://platform.openai.com/account/api-keys",
    )

    if st.button("Auto Generate Title and Description"):
        if st.session_state["ai_settings"]["api"]:
            if len(st.session_state["ai_settings"]["api"]) != 51:
                st.error("The API Key seems to be invalid, please provide another one")
            else:
                if st.session_state["content_data_new"]["detection"]:
                    detection_logic = json.dumps(
                        st.session_state["content_data_new"]["detection"]
                    )
                    if len(detection_logic) < 50:
                        st.error(
                            "The detection field must contains valid Sigma content"
                        )
                    else:
                        try:
                            # Generate Data
                            ai_data = sigma_title_desc(
                                st.session_state["ai_settings"]["api"],
                                detection_logic,
                            )

                            # Fill Data
                            st.session_state["content_data_new"]["title"] = ai_data[
                                "title"
                            ]

                            st.session_state["content_data_new"][
                                "description"
                            ] = ai_data["description"]

                            st.success(
                                "Successfully generated the Title and Description"
                            )
                        except openai.error.RateLimitError:
                            st.error(
                                "You exceeded your current quota, please check your plan and billing details."
                            )
                        except openai.error.AuthenticationError:
                            st.error(
                                "Incorrect API key provided. You can find your API key at https://platform.openai.com/account/api-keys."
                            )
                        except:
                            st.error("Unknown Error")

                else:
                    st.error("The detection field must not be empty")
        else:
            st.error("An OpenAI API Key is required to use the Auto Generate feature")

    st.title("Rule Metadata")

    # Title
    st.session_state["content_data_new"]["title"] = st.text_input(
        "Title", st.session_state["content_data_new"]["title"]
    )

    # Related
    st.session_state["content_data_new"]["related"][0]["id"] = st.text_input(
        "Related Id", st.session_state["content_data_new"]["related"][0]["id"]
    )

    related_type = ["", "derived", "merged", "obsoletes", "renamed", "similar"]
    st.session_state["content_data_new"]["related"][0]["type"] = st.selectbox(
        "Related Type",
        related_type,
        index=related_type.index(
            st.session_state["content_data_new"]["related"][0]["type"]
        )
        if st.session_state["content_data_new"]["related"][0]["type"] in related_type
        else 0,
    )

    # Status
    statuses = ["stable", "test", "experimental", "deprecated", "unsupported"]
    st.session_state["content_data_new"]["status"] = st.selectbox(
        "Status",
        statuses,
        index=statuses.index(st.session_state["content_data_new"]["status"])
        if st.session_state["content_data_new"]["status"] in statuses
        else 0,
    )

    # Description
    st.session_state["content_data_new"]["description"] = st.text_area(
        "Description", st.session_state["content_data_new"]["description"]
    )

    # References
    refs = st.text_area(
        "References (newline-separated)",
        "\n".join(st.session_state["content_data_new"]["references"]),
    )
    st.session_state["content_data_new"]["references"] = refs.split("\n")

    # Author
    st.session_state["content_data_new"]["author"] = st.text_input(
        "Author", st.session_state["content_data_new"]["author"]
    )

    # Date
    st.session_state["content_data_new"]["date"] = (
        st.date_input("Date", datetime.today())
    ).strftime("%Y/%m/%d")

    # Tags
    tags = st.text_area(
        "Tags (newline-separated)",
        "\n".join(st.session_state["content_data_new"]["tags"]),
    )
    st.session_state["content_data_new"]["tags"] = tags.split("\n")

    # Logsource

    # Product
    products = [""] + logsource_content["product"]
    try:
        _ = st.session_state["content_data_new"]["logsource"]["product"]
    except:
        st.session_state["content_data_new"]["logsource"]["product"] = ""

    st.session_state["content_data_new"]["logsource"]["product"] = st.selectbox(
        "product",
        products,
        help="Check the taxonomy tab for more information on the logsource mappings supported by Sigma",
        index=products.index(
            st.session_state["content_data_new"]["logsource"]["product"]
        )
        if st.session_state["content_data_new"]["logsource"]["product"] in products
        else 0,
    )

    # Service
    services = [""] + logsource_content["product"]
    try:
        _ = st.session_state["content_data_new"]["logsource"]["service"]
    except KeyError:
        st.session_state["content_data_new"]["logsource"]["service"] = ""

    st.session_state["content_data_new"]["logsource"]["service"] = st.selectbox(
        "service",
        services,
        help="Check the taxonomy tab for more information on the logsource mappings supported by Sigma",
        index=services.index(
            st.session_state["content_data_new"]["logsource"]["service"]
        )
        if st.session_state["content_data_new"]["logsource"]["service"] in services
        else 0,
    )

    # Category
    categories = [""] + logsource_content["category"]
    try:
        _ = st.session_state["content_data_new"]["logsource"]["category"]
    except KeyError:
        st.session_state["content_data_new"]["logsource"]["category"] = ""

    st.session_state["content_data_new"]["logsource"]["category"] = st.selectbox(
        "category",
        categories,
        help="Check the taxonomy tab for more information on the logsource mappings supported by Sigma",
        index=categories.index(
            st.session_state["content_data_new"]["logsource"]["category"]
        )
        if st.session_state["content_data_new"]["logsource"]["category"] in categories
        else 0,
    )

    # Falsepositives
    try:
        _ = st.session_state["content_data_new"]["falsepositives"]
    except KeyError:
        st.session_state["content_data_new"]["falsepositives"] = ""

    refs = st.text_area(
        "Falsepositives (newline-separated)",
        "\n".join(st.session_state["content_data_new"]["falsepositives"]),
    )
    st.session_state["content_data_new"]["falsepositives"] = refs.split("\n")

    # Level
    levels = ["informational", "low", "medium", "high", "critical"]
    st.session_state["content_data_new"]["level"] = st.selectbox(
        "Level",
        levels,
        index=levels.index(st.session_state["content_data_new"]["level"])
        if st.session_state["content_data_new"]["level"] in levels
        else 0,
    )


with tab1:
    st.markdown("### Detection", unsafe_allow_html=True)

    # Detection
    detection_str = yaml.safe_dump(
        st.session_state["content_data_new"]["detection"],
        default_flow_style=False,
        sort_keys=False,
        indent=4,
    )

    # tomorrow_night
    # dracula
    detection_content = st_ace(
        value=detection_str,
        language="yaml",
        theme="tomorrow_night",
        keybinding="vscode",
        wrap=False,
        font_size=15,
        tab_size=4,
    )

    # st.session_state["content_data_new"]["detection"] = st.text_area(
    #    "",
    #    detection_str,
    #    help="[Learn More](https://sigmahq.io/docs/basics/rules.html#detection)",
    # )

    st.session_state["content_data_new"]["detection"] = detection_content

    try:
        st.session_state["content_data_new"]["detection"] = yaml.safe_load(
            st.session_state["content_data_new"]["detection"]
        )
    except:
        st.error(
            "The detection section contains an error. Please make sure the syntax is correct"
        )

    st.markdown(
        "### Sigma YAML Output",
        unsafe_allow_html=True,
    )

    session_state_tmp = clean_empty(st.session_state["content_data_new"])

    # Just to make sure we don't dump unsafe code and at the same time enforce the indentation
    yaml_output_tmp = yaml.safe_dump(
        session_state_tmp,
        sort_keys=False,
        default_flow_style=False,
        indent=4,
        width=1000,
    )
    yaml_output_tmp = yaml.safe_load(yaml_output_tmp)

    yaml_output = yaml.dump(
        yaml_output_tmp,
        sort_keys=False,
        default_flow_style=False,
        Dumper=MyDumper,
        indent=4,
        width=1000,
    )

    st.code(yaml_output, language="yaml")

    st.markdown(
        """
            <style>
                div[data-testid="column"] {
                    width: fit-content !important;
                    flex: unset;
                }
                div[data-testid="column"] * {
                    width: fit-content !important;
                }
            </style>
            """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    generate_bool = False
    validate_bool = False

    with col1:
        if st.button("⚙️ Generate YAML File"):
            generate_bool = True

    with col2:
        if st.button("✔️ Validate Sigma Rule"):
            validate_bool = True

    with col3:
        # base64 and url encode the yaml output
        encoded_yaml_output = quote_plus(base64.b64encode(yaml_output.encode('utf-8')).decode('utf-8'))
        st.link_button(
            "⏳ Convert Using SigConverter",
            url="https://sigconverter.io/#rule=" + encoded_yaml_output,
        )

    if generate_bool:
        filename = "sigmahq_rule_" + str(uuid.uuid4()) + ".yml"
        st.success(f"{filename} Is Ready to Download!")
        st.info(
            f"Please don't forgot to follow the SigmaHQ file naming convention before contribution your rule https://github.com/SigmaHQ/sigma-specification/blob/main/sigmahq/Sigmahq_filename_rule.md"
        )
        download_button_str = st.download_button(
            label="Download YAML",
            data=yaml_output,
            file_name=filename,
            mime="text/yaml",
        )

        st.header("Contributing to SigmaHQ")
        st.markdown(
            """
                Congratulations! You've just generated a Sigma rule and you're only a few steps away from a great contribution. Please follow our [contribution guide](https://github.com/SigmaHQ/sigma/blob/master/CONTRIBUTING.md) to get started.
                """
        )

    if validate_bool:
        errors_num = 0

        # Title Test
        sigma_content = st.session_state["content_data_new"]
        try:
            title = sigma_content["title"]
            title_errors = test_title(title)
        except KeyError:
            title_errors = []
            st.warning(
                f"The rule has a missing 'title' field. Please check: https://github.com/SigmaHQ/sigma/wiki/Rule-Creation-Guide#title"
            )
        if title_errors:
            errors_num += 1
            error_msg = ""
            for err in title_errors:
                error_msg += "- " + err + "\n"
            st.warning(
                f"""
                    The rule has a non-conform 'title' field. Please check: https://github.com/SigmaHQ/sigma/wiki/Rule-Creation-Guide#title\n\n
                    {error_msg}
                    """
            )

        # False Positive Test
        sigma_content = st.session_state["content_data_new"]
        try:
            falsepositives = sigma_content["falsepositives"]
            falsepositives_errors = test_falsepositives(falsepositives)
        except KeyError:
            falsepositives_errors = []
            st.warning(f"The rule has a missing 'falsepositives' field.")
        if falsepositives_errors:
            errors_num += 1
            error_msg = ""
            for err in falsepositives_errors:
                error_msg += "- " + err + "\n"
            st.warning(
                f"""
                    The rule has a non-conform false positives section:\n\n
                    {error_msg}
                    """
            )

        # Logsource Test
        try:
            sigma_content = sigma_content["logsource"]
        except KeyError:
            errors_num += 1
            st.warning(
                "The rule has a missing 'logsource' field. Please check: https://sigmahq.io/docs/basics/log-sources.html"
            )

        if errors_num == 0:
            st.success("All tests have successfully passed")

with tab2:
    st.header("Getting Started")
    st.markdown(
        """
        If this is your first time writing a sigma rule. We highly recommend you check the following resources

        - 📚 [Writing You First Sigma Rule](https://sigmahq.io/docs/basics/rules.html)
        - 🧬 [What Are Value Modifiers?](https://sigmahq.io/docs/basics/modifiers.html)
        - 🔎 [Sigma Logsource](https://sigmahq.io/docs/basics/log-sources.html)
        - 🏷️ [Sigma Tags](https://github.com/SigmaHQ/sigma-specification/blob/main/Tags_specification.md)

        Make sure to follow the SigmaHQ conventions regarding the different fields for the best experience possible during the review process

        - [SigmaHQ Conventions](https://github.com/SigmaHQ/sigma-specification/blob/main/sigmahq/sigmahq_conventions.md)    
        - [SigmaHQ Rule Title Convention](https://github.com/SigmaHQ/sigma-specification/blob/main/sigmahq/sigmahq_title_rule.md)
        """
    )

with tab3:
    with open("streamlit/taxonomy.md", "r") as f:
        content = f.read()
    st.markdown(content, unsafe_allow_html=True)