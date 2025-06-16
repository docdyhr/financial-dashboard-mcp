"""ISIN input component for financial dashboard frontend."""

import logging
import re

import requests
import streamlit as st

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"


def validate_isin_format(isin: str) -> tuple[bool, str]:
    """Validate ISIN format locally before sending to backend.

    Args:
        isin: The ISIN code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isin:
        return False, "ISIN cannot be empty"

    isin = isin.upper().strip()

    # Basic format validation
    if len(isin) != 12:
        return False, "ISIN must be exactly 12 characters"

    if not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", isin):
        return False, "ISIN format: 2 letters + 9 alphanumeric + 1 digit"

    return True, ""


def call_isin_api(endpoint: str, data: dict) -> dict | None:
    """Call ISIN API endpoint with error handling.

    Args:
        endpoint: API endpoint path
        data: Request data

    Returns:
        API response data or None if error
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/isin/{endpoint}", json=data, timeout=10
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"API Error {response.status_code}: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


def isin_input_widget(
    key: str = "isin_input",
    label: str = "Enter ISIN Code",
    help_text: str = "International Securities Identification Number (12 characters)",
    auto_lookup: bool = True,
    show_suggestions: bool = True,
) -> dict | None:
    """ISIN input widget with validation and ticker lookup.

    Args:
        key: Unique key for the widget
        label: Label for the input field
        help_text: Help text shown below the input
        auto_lookup: Whether to automatically lookup ticker when ISIN is entered
        show_suggestions: Whether to show ticker format suggestions

    Returns:
        Dictionary with ISIN info if valid, None otherwise
    """
    st.subheader("🔢 ISIN Input")

    col1, col2 = st.columns([3, 1])

    with col1:
        isin = (
            st.text_input(
                label,
                key=key,
                help=help_text,
                placeholder="e.g., US0378331005 (Apple Inc.)",
                max_chars=12,
            )
            .upper()
            .strip()
        )

    with col2:
        validate_button = st.button("Validate", key=f"{key}_validate")

    if not isin:
        return None

    # Real-time format validation
    is_valid_format, format_error = validate_isin_format(isin)

    if not is_valid_format:
        st.error(f"❌ Invalid format: {format_error}")
        return None

    # Show ISIN structure info
    with st.expander("ℹ️ ISIN Structure", expanded=False):
        country_code = isin[:2]
        national_code = isin[2:11]
        check_digit = isin[11]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Country Code", country_code)
        with col2:
            st.metric("National Code", national_code)
        with col3:
            st.metric("Check Digit", check_digit)

    # Validate with backend if auto_lookup is enabled or validate button is clicked
    if auto_lookup or validate_button:
        with st.spinner("🔍 Validating ISIN..."):
            validation_result = call_isin_api("validate", {"isin": isin})

            if validation_result:
                if validation_result.get("is_valid"):
                    st.success(f"✅ Valid ISIN: {isin}")

                    # Show country information
                    if validation_result.get("country_name"):
                        st.info(
                            f"🌍 Country: {validation_result['country_name']} ({validation_result.get('country_code', 'N/A')})"
                        )

                    # Lookup ticker mappings
                    with st.spinner("🎯 Looking up ticker symbols..."):
                        lookup_result = call_isin_api(
                            "lookup", {"isins": [isin], "prefer_primary_exchange": True}
                        )

                        if lookup_result and lookup_result.get("results"):
                            isin_data = lookup_result["results"].get(isin, {})

                            if isin_data.get("found"):
                                # Show ticker mappings
                                st.success("🎯 Ticker mappings found!")

                                mappings = isin_data.get("mappings", [])
                                if mappings:
                                    st.subheader("📊 Available Ticker Symbols")

                                    for mapping in mappings:
                                        with st.container():
                                            col1, col2, col3, col4 = st.columns(
                                                [2, 2, 2, 1]
                                            )

                                            with col1:
                                                st.write(
                                                    f"**{mapping.get('ticker', 'N/A')}**"
                                                )
                                            with col2:
                                                st.write(
                                                    mapping.get("exchange_name", "N/A")
                                                )
                                            with col3:
                                                st.write(mapping.get("currency", "N/A"))
                                            with col4:
                                                confidence = mapping.get(
                                                    "confidence", 0
                                                )
                                                st.metric(
                                                    "Confidence", f"{confidence:.1%}"
                                                )

                                # Return comprehensive data
                                return {
                                    "isin": isin,
                                    "is_valid": True,
                                    "country_code": validation_result.get(
                                        "country_code"
                                    ),
                                    "country_name": validation_result.get(
                                        "country_name"
                                    ),
                                    "mappings": mappings,
                                    "primary_ticker": (
                                        mappings[0].get("ticker") if mappings else None
                                    ),
                                    "primary_exchange": (
                                        mappings[0].get("exchange_code")
                                        if mappings
                                        else None
                                    ),
                                }
                            st.warning("⚠️ No ticker mappings found for this ISIN")

                            # Show ticker suggestions if enabled
                            if show_suggestions:
                                st.subheader("💡 Ticker Format Suggestions")

                                suggestion_result = call_isin_api(
                                    "suggestions",
                                    {"isin": isin, "max_suggestions": 5},
                                )

                                if suggestion_result and suggestion_result.get(
                                    "suggestions"
                                ):
                                    for suggestion in suggestion_result[
                                        "suggestions"
                                    ]:
                                        st.info(
                                            f"💡 Try: {suggestion.get('ticker')} ({suggestion.get('explanation', 'No explanation')})"
                                        )

                            return {
                                "isin": isin,
                                "is_valid": True,
                                "country_code": validation_result.get(
                                    "country_code"
                                ),
                                "country_name": validation_result.get(
                                    "country_name"
                                ),
                                "mappings": [],
                                "primary_ticker": None,
                                "primary_exchange": None,
                            }
                        st.error("❌ Failed to lookup ticker mappings")
                else:
                    st.error(
                        f"❌ Invalid ISIN: {validation_result.get('error', 'Unknown error')}"
                    )
            else:
                st.error("❌ Failed to validate ISIN")

    return None


def isin_to_ticker_converter(key: str = "isin_converter") -> None:
    """ISIN to ticker converter widget.

    Args:
        key: Unique key for the widget
    """
    st.subheader("🔄 ISIN to Ticker Converter")

    with st.form(key=f"{key}_form"):
        isin_input = (
            st.text_input(
                "ISIN Code",
                placeholder="Enter ISIN to convert to ticker",
                max_chars=12,
                key=f"{key}_input",
            )
            .upper()
            .strip()
        )

        prefer_exchange = st.selectbox(
            "Prefer Exchange",
            options=["", "XNAS", "XNYS", "XETR", "XLON", "XTSE", "XJPX"],
            help="Prefer ticker from specific exchange (optional)",
        )

        convert_button = st.form_submit_button("Convert")

    if convert_button and isin_input:
        is_valid, error = validate_isin_format(isin_input)

        if not is_valid:
            st.error(f"❌ {error}")
            return

        with st.spinner("🔄 Converting ISIN to ticker..."):
            resolution_result = call_isin_api(
                "resolve",
                {
                    "identifier": isin_input,
                    "prefer_exchange": prefer_exchange if prefer_exchange else None,
                },
            )

            if resolution_result:
                if resolution_result.get("found"):
                    result = resolution_result.get("result", {})
                    ticker = result.get("ticker")
                    identifier_type = result.get("type")

                    if ticker:
                        st.success(
                            f"✅ **{isin_input}** → **{ticker}** ({identifier_type})"
                        )

                        # Show additional info
                        if result.get("info"):
                            info = result["info"]
                            col1, col2 = st.columns(2)

                            with col1:
                                if info.get("country_name"):
                                    st.info(f"🌍 Country: {info['country_name']}")
                            with col2:
                                if result.get("exchange"):
                                    st.info(f"🏢 Exchange: {result['exchange']}")
                    else:
                        st.warning("⚠️ ISIN found but no ticker available")
                else:
                    st.error("❌ Could not resolve ISIN to ticker")
            else:
                st.error("❌ Failed to resolve ISIN")


def bulk_isin_lookup(key: str = "bulk_lookup") -> None:
    """Bulk ISIN lookup widget.

    Args:
        key: Unique key for the widget
    """
    st.subheader("📋 Bulk ISIN Lookup")

    with st.form(key=f"{key}_form"):
        isin_list_text = st.text_area(
            "ISIN List (one per line)",
            placeholder="US0378331005\nGB0002162385\nDE0007164600",
            height=150,
            key=f"{key}_textarea",
        )

        col1, col2 = st.columns(2)
        with col1:
            prefer_primary = st.checkbox("Prefer Primary Exchange", value=True)
        with col2:
            include_inactive = st.checkbox("Include Inactive Mappings", value=False)

        lookup_button = st.form_submit_button("Lookup All")

    if lookup_button and isin_list_text:
        # Parse ISIN list
        isin_list = [
            line.strip().upper() for line in isin_list_text.split("\n") if line.strip()
        ]

        if not isin_list:
            st.error("❌ No valid ISINs found")
            return

        # Validate all ISINs first
        valid_isins = []
        invalid_isins = []

        for isin in isin_list:
            is_valid, _ = validate_isin_format(isin)
            if is_valid:
                valid_isins.append(isin)
            else:
                invalid_isins.append(isin)

        if invalid_isins:
            st.error(f"❌ Invalid ISINs found: {', '.join(invalid_isins)}")

        if not valid_isins:
            st.error("❌ No valid ISINs to lookup")
            return

        st.info(f"🔍 Looking up {len(valid_isins)} valid ISINs...")

        with st.spinner("📡 Performing bulk lookup..."):
            lookup_result = call_isin_api(
                "lookup",
                {
                    "isins": valid_isins,
                    "prefer_primary_exchange": prefer_primary,
                    "include_inactive": include_inactive,
                },
            )

            if lookup_result and lookup_result.get("results"):
                results = lookup_result["results"]

                # Display results
                st.subheader("📊 Lookup Results")

                found_count = sum(1 for r in results.values() if r.get("found"))
                st.metric("Found", f"{found_count}/{len(valid_isins)}")

                # Results table
                results_data = []
                for isin in valid_isins:
                    result = results.get(isin, {})
                    if result.get("found"):
                        mappings = result.get("mappings", [])
                        primary_mapping = mappings[0] if mappings else {}

                        results_data.append(
                            {
                                "ISIN": isin,
                                "Ticker": primary_mapping.get("ticker", "N/A"),
                                "Exchange": primary_mapping.get("exchange_name", "N/A"),
                                "Currency": primary_mapping.get("currency", "N/A"),
                                "Confidence": f"{primary_mapping.get('confidence', 0):.1%}",
                                "Status": "✅ Found",
                            }
                        )
                    else:
                        results_data.append(
                            {
                                "ISIN": isin,
                                "Ticker": "N/A",
                                "Exchange": "N/A",
                                "Currency": "N/A",
                                "Confidence": "N/A",
                                "Status": "❌ Not Found",
                            }
                        )

                if results_data:
                    st.dataframe(results_data, use_container_width=True)

            else:
                st.error("❌ Failed to perform bulk lookup")


def isin_management_page():
    """Complete ISIN management page combining all widgets.
    """
    st.title("🔢 ISIN Management")
    st.markdown("*International Securities Identification Number tools*")

    tab1, tab2, tab3 = st.tabs(["🔍 Single ISIN", "🔄 Converter", "📋 Bulk Lookup"])

    with tab1:
        result = isin_input_widget()
        if result:
            st.session_state.last_isin_result = result

    with tab2:
        isin_to_ticker_converter()

    with tab3:
        bulk_isin_lookup()

    # Show last result in sidebar
    if (
        hasattr(st.session_state, "last_isin_result")
        and st.session_state.last_isin_result
    ):
        with st.sidebar:
            st.subheader("📌 Last ISIN Result")
            result = st.session_state.last_isin_result
            st.code(result["isin"])
            if result.get("primary_ticker"):
                st.success(f"Primary: {result['primary_ticker']}")
            if result.get("country_name"):
                st.info(f"Country: {result['country_name']}")
