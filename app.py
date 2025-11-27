import streamlit as st
import pandas as pd
from datetime import datetime, time
import uuid
from typing import List, Dict, Any

# --- Configuration ---
st.set_page_config(
    page_title="Event Management System",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom styling (optional, Streamlit's dark theme handles most of it)
st.markdown("""
    <style>
        .st-emotion-cache-18ni7ap { /* Main content padding fix */
            padding-top: 1rem;
        }
        .st-emotion-cache-10trblm { /* Header alignment */
            text-align: left;
            padding-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---

if 'events' not in st.session_state:
    # Initialize with some dummy data to showcase the structure
    st.session_state.events = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Annual Tech Summit',
            'date': datetime(2025, 12, 10).date(),
            'time': datetime(2025, 12, 10, 9, 30).time(),
            'location': 'City Convention Center',
            'attendees': 500,
            'budget': 15000.00,
            'status': 'Planned'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Client Appreciation Dinner',
            'date': datetime(2025, 11, 28).date(),
            'time': datetime(2025, 11, 28, 18, 0).time(),
            'location': 'The Grand Ballroom',
            'attendees': 85,
            'budget': 4200.00,
            'status': 'Booked'
        }
    ]

if 'page' not in st.session_state:
    st.session_state.page = 'Add Event'

if 'editing_event_id' not in st.session_state:
    st.session_state.editing_event_id = None


# Convert event list to DataFrame for easy manipulation
def get_events_df() -> pd.DataFrame:
    if not st.session_state.events:
        return pd.DataFrame(columns=['ID', 'Name', 'Date', 'Time', 'Location', 'Attendees', 'Budget', 'Status'])
    
    df = pd.DataFrame(st.session_state.events)
    # Format Budget column
    df['Budget'] = df['budget'].apply(lambda x: f"${x:,.2f}")
    # Select and rename columns for display
    df_display = df.rename(columns={
        'id': 'ID', 
        'name': 'Name', 
        'date': 'Date', 
        'time': 'Time', 
        'location': 'Location', 
        'attendees': 'Attendees',
        'status': 'Status'
    })
    return df_display[['ID', 'Name', 'Date', 'Time', 'Location', 'Attendees', 'Budget', 'Status']]


# --- Event Management Functions ---

def add_new_event(data: Dict[str, Any]):
    """Adds a new event to the session state."""
    new_event = {
        'id': str(uuid.uuid4()),
        'name': data['name'],
        'date': data['date'],
        'time': data['time'],
        'location': data['location'],
        'attendees': data['attendees'],
        'budget': data['budget'],
        'status': data.get('status', 'Planned') # Allows setting status for new event
    }
    st.session_state.events.append(new_event)
    st.success(f"Event '{data['name']}' added successfully!")
    st.session_state.page = 'View & Sort Events' # Navigate to view events
    st.rerun()

def delete_event(event_id: str):
    """Deletes an event by its ID."""
    initial_count = len(st.session_state.events)
    st.session_state.events = [e for e in st.session_state.events if e['id'] != event_id]
    if len(st.session_state.events) < initial_count:
        st.success("Event deleted successfully.")
        st.session_state.editing_event_id = None # Clear editing state if deleted
    else:
        st.error("Error deleting event. ID not found.")
    st.rerun()

def edit_event(event_id: str, new_data: Dict[str, Any]):
    """Updates an existing event's data."""
    found = False
    for i, event in enumerate(st.session_state.events):
        if event['id'] == event_id:
            # Update the event fields
            st.session_state.events[i].update({
                'name': new_data['name'],
                'date': new_data['date'],
                'time': new_data['time'],
                'location': new_data['location'],
                'attendees': new_data['attendees'],
                'budget': new_data['budget'],
                'status': new_data['status'],
            })
            found = True
            break
            
    if found:
        st.success(f"Event '{new_data['name']}' updated successfully!")
        st.session_state.editing_event_id = None # Exit edit mode
    else:
        st.error("Error: Event ID not found during update.")
    st.rerun()


# --- View Functions ---

def add_event_view():
    """Displays the form for adding a new event."""
    st.title("➕ Add New Event")
    st.markdown("---")
    
    # FIX APPLIED HERE: Changed "key='add_event_form_key" to key='add_event_form_key'
    with st.form(key='add_event_form_key', clear_on_submit=True):
        st.subheader("Event Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name", placeholder="e.g., Annual Sales Kickoff", required=True)
            event_date = st.date_input("Date", datetime.now().date(), required=True)
            event_location = st.text_input("Location", placeholder="e.g., Conference Room A", required=True)
            event_status = st.selectbox("Status", options=['Planned', 'Booked', 'Complete', 'Cancelled'], index=0)

        with col2:
            event_time = st.time_input("Time", datetime.now().time())
            event_attendees = st.number_input("Expected Attendees", min_value=1, value=100)
            event_budget = st.number_input("Budget (USD)", min_value=0.00, value=1000.00, step=100.00, format="%.2f")

        st.markdown("---")
        submitted = st.form_submit_button("Submit Event", use_container_width=True)
        
        if submitted:
            if event_name and event_date and event_location:
                add_new_event({
                    'name': event_name,
                    'date': event_date,
                    'time': event_time,
                    'location': event_location,
                    'attendees': event_attendees,
                    'budget': event_budget,
                    'status': event_status
                })
            else:
                st.error("Please fill in all required fields (Name, Date, Location).")


def view_sort_events_view():
    """Displays all events with sorting, editing, and deletion options."""
    st.title("📋 Manage & Sort Events")
    st.markdown("---")

    events_list = st.session_state.events
    events_df = get_events_df()
    
    if events_df.empty:
        st.info("No events have been added yet.")
        return

    # --- Sorting ---
    col1, col2 = st.columns([1, 4])
    with col1:
        sort_by = st.selectbox(
            "Sort By:",
            options=['Date (Newest first)', 'Date (Oldest first)', 'Attendees (High to Low)', 'Name (A-Z)'],
            key='sort_select'
        )

    # Apply sorting logic
    df_to_sort = pd.DataFrame(events_list)
    
    if sort_by == 'Date (Newest first)':
        df_sorted = df_to_sort.sort_values(by='date', ascending=False)
    elif sort_by == 'Date (Oldest first)':
        df_sorted = df_to_sort.sort_values(by='date', ascending=True)
    elif sort_by == 'Attendees (High to Low)':
        df_sorted = df_to_sort.sort_values(by='attendees', ascending=False)
    elif sort_by == 'Name (A-Z)':
        df_sorted = df_to_sort.sort_values(by='name', ascending=True)

    # Prepare for display again
    df_display_sorted = df_sorted.rename(columns={
        'id': 'ID', 
        'name': 'Name', 
        'date': 'Date', 
        'time': 'Time', 
        'location': 'Location', 
        'attendees': 'Attendees',
        'status': 'Status'
    })
    df_display_sorted['Budget'] = df_display_sorted['budget'].apply(lambda x: f"${x:,.2f}")
    df_final = df_display_sorted[['ID', 'Name', 'Date', 'Time', 'Location', 'Attendees', 'Budget', 'Status']]
    
    st.subheader("All Events")

    st.dataframe(df_final.set_index('ID'), use_container_width=True, height=len(df_final) * 35 + 38)
    
    st.markdown("---")

    # --- Edit Event Section ---
    st.subheader("✏️ Edit Event")
    
    event_names = {e['id']: f"{e['name']} ({e['date']})" for e in events_list}
    event_id_options = ['-- Select Event to Edit --'] + list(event_names.keys())
    
    # Get the index for the currently editing event ID for the selectbox
    try:
        default_index = event_id_options.index(st.session_state.editing_event_id)
    except ValueError:
        default_index = 0

    selected_edit_id = st.selectbox(
        "Choose an event to modify:",
        options=event_id_options,
        format_func=lambda id: event_names.get(id, id) if id != '-- Select Event to Edit --' else id,
        index=default_index,
        key='edit_select'
    )

    if selected_edit_id != '-- Select Event to Edit --':
        st.session_state.editing_event_id = selected_edit_id
        
        # Find the event data
        current_event = next(e for e in events_list if e['id'] == selected_edit_id)
        
        # Display the edit form in an expander
        with st.expander(f"Editing: {current_event['name']}", expanded=True):
            with st.form(f"edit_event_form_{selected_edit_id}"):
                
                col_e1, col_e2 = st.columns(2)
                
                # Find the index of the current status for the selectbox
                status_options = ['Planned', 'Booked', 'Complete', 'Cancelled']
                default_status_index = status_options.index(current_event.get('status', 'Planned'))

                with col_e1:
                    edit_name = st.text_input("Event Name", value=current_event['name'], required=True, key='edit_name')
                    edit_date = st.date_input("Date", value=current_event['date'], required=True, key='edit_date')
                    edit_location = st.text_input("Location", value=current_event['location'], required=True, key='edit_location')
                
                with col_e2:
                    # Time input expects a datetime.time object
                    edit_time = st.time_input("Time", value=current_event['time'], key='edit_time')
                    edit_attendees = st.number_input("Expected Attendees", min_value=1, value=current_event['attendees'], key='edit_attendees')
                    edit_budget = st.number_input("Budget (USD)", min_value=0.00, value=current_event['budget'], step=100.00, format="%.2f", key='edit_budget')
                    
                    edit_status = st.selectbox("Status", options=status_options, index=default_status_index, key='edit_status')
                
                edit_submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                
                if edit_submitted:
                    edit_event(selected_edit_id, {
                        'name': edit_name,
                        'date': edit_date,
                        'time': edit_time,
                        'location': edit_location,
                        'attendees': edit_attendees,
                        'budget': edit_budget,
                        'status': edit_status
                    })
    
    # --- Delete Event Section (Original) ---
    st.markdown("---")
    st.subheader("❌ Delete Event")
    st.warning("Enter the full ID of the event you wish to delete. This action cannot be undone.")
    
    event_id_to_delete = st.text_input("Event ID to Delete", placeholder="Paste event ID here")
    
    if st.button("Delete Selected Event", type="secondary", help="Deletes the event permanently"):
        # We need to use the original list of IDs for a valid check
        if event_id_to_delete in [e['id'] for e in st.session_state.events]:
            delete_event(event_id_to_delete)
        else:
            st.error("Invalid Event ID or event not found.")


def search_events_view():
    """Displays search functionality and results."""
    st.title("🔎 Search Events")
    st.markdown("---")
    
    events_list = st.session_state.events
    events_df = pd.DataFrame(events_list)
    
    if events_df.empty:
        st.info("No events to search.")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        search_field = st.selectbox(
            "Search By:",
            options=['name', 'location']
        )
    
    with col2:
        search_term = st.text_input(
            f"Enter Search Term ({search_field.capitalize()})", 
            placeholder=f"e.g., Dinner or Convention"
        )
    
    st.markdown("---")

    if search_term:
        st.subheader(f"Results for '{search_term}'")
        
        # Filter the DataFrame
        search_term_lower = search_term.lower()
        
        if search_field == 'name':
            filtered_df = events_df[events_df['name'].str.lower().str.contains(search_term_lower, na=False)]
        elif search_field == 'location':
            filtered_df = events_df[events_df['location'].str.lower().str.contains(search_term_lower, na=False)]
        
        if filtered_df.empty:
            st.warning(f"No events found matching '{search_term}' in the {search_field} field.")
        else:
            # Prepare filtered data for display
            df_display = filtered_df.rename(columns={
                'id': 'ID', 
                'name': 'Name', 
                'date': 'Date', 
                'time': 'Time', 
                'location': 'Location', 
                'attendees': 'Attendees',
                'status': 'Status'
            })
            df_display['Budget'] = df_display['budget'].apply(lambda x: f"${x:,.2f}")
            df_final = df_display[['ID', 'Name', 'Date', 'Time', 'Location', 'Attendees', 'Budget', 'Status']]
            
            st.dataframe(df_final.set_index('ID'), use_container_width=True)
            
    else:
        st.info("Enter a search term above to filter events.")


# --- Main App Logic (Sidebar Navigation) ---

# Sidebar Title
st.sidebar.title("Event Manager")
st.sidebar.markdown("---")

# Navigation Selector
page = st.sidebar.radio(
    "Select an Option",
    options=['Add Event', 'View & Sort Events', 'Search Events'],
    index=['Add Event', 'View & Sort Events', 'Search Events'].index(st.session_state.page) if st.session_state.page in ['Add Event', 'View & Sort Events', 'Search Events'] else 0,
    key='main_nav'
)

st.session_state.page = page

st.sidebar.markdown("---")
st.sidebar.info("Data is stored in memory (`st.session_state`) and is not persistent across sessions. For production, connect to a database like Firestore.")

# Render the selected view
if st.session_state.page == 'Add Event':
    add_event_view()
elif st.session_state.page == 'View & Sort Events':
    view_sort_events_view()
elif st.session_state.page == 'Search Events':
    search_events_view()
