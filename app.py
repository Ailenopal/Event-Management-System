import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from typing import List, Dict, Any

# --- Configuration and Initialization ---

# Set page configuration for better aesthetics (simulating dark mode)
st.set_page_config(
    page_title="Streamlit Event Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'events' not in st.session_state:
    st.session_state.events = []

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'add-event' # Default view

# NEW: State to track the last added event for highlighting
if 'last_added_id' not in st.session_state:
    st.session_state.last_added_id = None

# --- Utility Functions ---

def generate_unique_id() -> str:
    """Generates a unique ID for an event."""
    return str(uuid.uuid4())

def set_view(view_name: str):
    """Sets the current view in the session state and clears highlight."""
    st.session_state.current_view = view_name
    # Clear the highlight state when navigating manually
    st.session_state.last_added_id = None 
    st.rerun()

# *** IMPROVED add_new_event for automatic view change and highlight ***
def add_new_event(event_data: Dict[str, Any]):
    """
    Adds a new event, sets the view to 'view-events', and highlights the new event.
    """
    # Check for required fields again (though form submission logic also checks)
    if not event_data['name'] or not event_data['location']:
        st.error("Event Name and Location are required.")
        return False

    # Create the datetime object for sorting
    try:
        # st.time_input returns a time object which gets converted to H:M:S string
        datetime_obj = datetime.strptime(
            f"{event_data['date']} {event_data['time']}", 
            '%Y-%m-%d %H:%M:%S'
        )
    except ValueError:
        st.error("Error creating event datetime. Check date and time format.")
        return False
        
    unique_id = generate_unique_id()
    
    new_event = {
        'id': unique_id,
        'name': event_data['name'],
        'date': event_data['date'],
        'time': event_data['time'],
        'location': event_data['location'],
        'attendees': event_data['attendees'],
        'budget': event_data['budget'],
        'datetime_obj': datetime_obj
    }
    
    st.session_state.events.append(new_event)
    
    # 1. Store the ID for highlighting
    st.session_state.last_added_id = unique_id
    
    # 2. Set the new view
    st.session_state.current_view = 'view-events'
    
    # 3. Show success notification (st.toast is less intrusive than st.success)
    st.toast(f"Event '{new_event['name']}' added! Navigating to list. 🎉", icon='✅')
    
    st.rerun() 
    return True

def delete_event(event_id: str):
    """Deletes an event by ID from the session state."""
    initial_length = len(st.session_state.events)
    st.session_state.events = [event for event in st.session_state.events if event['id'] != event_id]
    
    # Clear highlight if the deleted event was the last highlighted one
    if st.session_state.last_added_id == event_id:
        st.session_state.last_added_id = None
        
    if len(st.session_state.events) < initial_length:
        st.toast("Event deleted successfully. 🗑️", icon='✅')
        st.rerun() # Rerun to update the displayed list
    else:
        st.error("Error: Event not found or deletion failed.")
        
# --- Data Preparation for Display ---

def get_events_dataframe(events: List[Dict[str, Any]], sort_by: str = 'date-asc') -> pd.DataFrame:
    """Converts event list to a sorted DataFrame for display."""
    if not events:
        return pd.DataFrame()
        
    df = pd.DataFrame(events)
    
    # Prepare display columns
    df['Date/Time'] = df['date'] + ' at ' + df['time'].str[:5] # Truncate time to HH:MM for display
    df['Budget (PESO)'] = df['budget'].apply(lambda x: f"${x:,.2f}")
    df['Attendees'] = df['attendees'].apply(lambda x: f"{x:,}")
    # ID is kept for internal reference, not displayed
    df['Sort_Key'] = df['datetime_obj']

    # Sorting
    if sort_by == 'date-desc':
        df = df.sort_values(by='Sort_Key', ascending=False)
    elif sort_by == 'attendees-desc':
        df = df.sort_values(by='attendees', ascending=False)
    elif sort_by == 'name-asc':
        df = df.sort_values(by='name', ascending=True)
    else: # date-asc (default)
        df = df.sort_values(by='Sort_Key', ascending=True)
    
    df['#'] = range(1, len(df) + 1) # Add index column for UI
    
    # Only return columns needed for display and the internal ID
    return df[['#', 'name', 'Date/Time', 'location', 'Attendees', 'Budget (PESO)', 'id']]

# --- UI Components (Views) ---

def add_event_view():
    """Renders the Add Event form."""
    st.markdown("## Add New Event")
    
    # Use st.form to ensure all inputs are cleared on submission
    with st.form("add_event_form"):
        # Initial values can be set here if not using keys to persist state
        st.text_input("Event Name", key="event-name")
        
        col_dt_1, col_dt_2 = st.columns(2)
        with col_dt_1:
            st.date_input("Date", datetime.today().date(), key="event-date")
        with col_dt_2:
            st.time_input("Time", datetime.now().time(), key="event-time")

        st.text_input("Location", key="event-location")

        col_num_1, col_num_2 = st.columns(2)
        with col_num_1:
            st.number_input("Expected Attendees", min_value=1, value=10, step=1, key="event-attendees")
        with col_num_2:
            st.number_input("Budget (PESO)", min_value=0.0, value=10.00, step=0.01, format="%.2f", key="event-budget")
            
        submitted = st.form_submit_button("Add Event", type="primary", use_container_width=True)
        
        if submitted:
            # Gather data from session state keys used above
            event_data = {
                # Convert date/time objects to string for consistent storage
                'name': st.session_state['event-name'],
                'date': str(st.session_state['event-date']),
                'time': str(st.session_state['event-time']),
                'location': st.session_state['event-location'],
                # number_input returns int/float, so pass them directly
                'attendees': st.session_state['event-attendees'],
                'budget': st.session_state['event-budget'],
            }
            if event_data['name'] and event_data['location']:
                # The function now handles the rerun and view change
                add_new_event(event_data)
            else:
                st.error("Event Name and Location are required.")


# *** IMPROVED view_events_view for highlighting ***
def view_events_view():
    """Renders the View & Sort Events table, including highlighting."""
    st.markdown("## Manage & Sort Events")

    sort_option = st.selectbox(
        "Sort By:",
        options=['date-asc', 'date-desc', 'attendees-desc', 'name-asc'],
        format_func=lambda x: {
            'date-asc': 'Date (Oldest first)',
            'date-desc': 'Date (Newest first)',
            'attendees-desc': 'Attendees (High to Low)',
            'name-asc': 'Name (A-Z)'
        }[x],
        key="sort-by"
    )
    
    st.markdown("---")
    
    events_df = get_events_dataframe(st.session_state.events, sort_option)
    
    if events_df.empty:
        st.info("No events found. Navigate to 'Add Event' to create one.")
    else:
        # Define the style function to highlight the last added event
        last_added_id = st.session_state.last_added_id
        
        def highlight_new_event(row):
            """Applies CSS styling to highlight the row of the last added event."""
            is_new = row['id'] == last_added_id
            # Streamlit dataframe uses the style property for the whole row (TR)
            # Use 'background-color' for a clear highlight
            style = 'background-color: rgba(0, 255, 0, 0.1); border: 2px solid green;' if is_new else ''
            return [style] * len(row)
            
        # Clear the highlight state *after* preparing the highlight function
        # This allows the highlight to persist across the rerun if the user changes the sort option
        if last_added_id:
             # Show a helper message for the highlight
             st.info(f"The event with ID: **{last_added_id[:8]}...** has been successfully added and is **highlighted in green** below.")
        
        # Use a container for the table and actions
        with st.container(border=True):
            st.markdown("### All Events")
            
            # Prepare columns for the table display
            display_df = events_df[['#', 'name', 'Date/Time', 'location', 'Attendees', 'Budget (PESO)', 'id']]
            
            # Display the table itself (read-only for all columns)
            st.dataframe(
                # Use the 'id' column for styling but hide it from the user
                display_df.style.apply(highlight_new_event, axis=1),
                column_config={"id": st.column_config.Column(disabled=True, visible=False)},
                hide_index=True,
                use_container_width=True,
            )
            
            # Clear the highlight after it has been displayed once in the View Events view
            # This ensures that if the user clicks back to 'Add Event' and then 'View Events', 
            # the highlight is gone unless a new event was added.
            st.session_state.last_added_id = None 

            st.markdown("---")
            st.markdown("#### Delete Actions")
            
            # Create a separate loop to generate delete buttons
            for index, row in events_df.iterrows():
                col_name, col_delete = st.columns([4, 1])
                with col_name:
                    st.text(f"Event {row['#']}: {row['name']} (ID: {row['id'][:8]}...)")
                with col_delete:
                    # Use on_click callback to trigger deletion and immediate rerun
                    st.button(
                        "Delete", 
                        key=f"delete-{row['id']}", 
                        type="secondary",
                        help=f"Delete event: {row['name']}",
                        on_click=delete_event, 
                        args=(row['id'],) # Pass the event ID to the function
                    )


def search_events_view():
    """Renders the Search Events form and results."""
    # Ensure highlight is clear on manual navigation
    st.session_state.last_added_id = None 
    
    st.markdown("## Search Events")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        search_field = st.selectbox(
            "Search By:",
            options=['name', 'location'],
            format_func=lambda x: {'name': 'Event Name', 'location': 'Location'}[x],
            key="search-field"
        )
    with col2:
        search_term = st.text_input("Enter Search Term", placeholder="e.g., Tech Summit", key="search-term")
        
    with col3:
        # Add some space for vertical alignment
        st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True) 
        # Set a key for the button to check if it was clicked
        st.button("Search", key="execute-search")
    
    st.markdown("---")
    st.markdown("### Search Results")

    # Check the button's state in session state
    # st.button returns True on click, which is stored in session state if a key is used
    search_clicked = st.session_state.get("execute-search", False) 
    
    # Only run search logic if the button was clicked AND a term is entered
    if search_clicked and st.session_state['search-term']:
        term_lower = st.session_state['search-term'].lower().strip()
        search_field = st.session_state['search-field']

        filtered_events = [
            event for event in st.session_state.events 
            if term_lower in str(event.get(search_field, '') or '').lower()
        ]
        
        if not filtered_events:
            st.info(f"No events found matching '{st.session_state['search-term']}' in {search_field}.")
        else:
            search_df = get_events_dataframe(filtered_events)
            
            st.dataframe(
                search_df[['#', 'name', 'Date/Time', 'location', 'Attendees']],
                hide_index=True,
                use_container_width=True
            )

    else:
        st.info("Enter a search term and click 'Search' to view results.")


# --- Main Application Layout ---

# Sidebar Navigation (Replicating the HTML sidebar)
with st.sidebar:
    st.markdown("# Event Manager")
    st.markdown("---")
    st.markdown("### Select an option")
    
    # Define a button style helper
    def nav_button(label, view_id, icon):
        # Use on_click to set the view and st.rerun to refresh immediately
        st.button(
            f"{icon} {label}", 
            on_click=set_view, args=(view_id,), 
            use_container_width=True,
            type="primary" if st.session_state.current_view == view_id else "secondary"
        )

    nav_button("Add Event", 'add-event', '📅')
    nav_button("View & Sort Events", 'view-events', '📋')
    nav_button("Search Events", 'search-events', '🔍')

# Main Content Area
st.title("Event Management System (Session State)")
st.markdown("---")

# Render the active view based on session state
if st.session_state.current_view == 'add-event':
    add_event_view()
elif st.session_state.current_view == 'view-events':
    view_events_view()
elif st.session_state.current_view == 'search-events':
    search_events_view()
