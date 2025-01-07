import streamlit as st
import pandas as pd
import os


class QuestionDatabaseApp:
    def __init__(self, db_file="sample_db.csv", topics_file="sample_topics.csv"):
        self.db_file = db_file
        self.topics_file = topics_file
        self.df = self.load_database()
        self.topics, self.subtopics = self.load_topics_and_subtopics()

    def load_database(self):
        """
        Load the question database from the CSV file or initialize a new DataFrame if it doesn't exist.
        """
        if os.path.exists(self.db_file):
            return pd.read_csv(self.db_file)
        else:
            return pd.DataFrame(columns=[
                'Custom_Question_ID', 'Topic', 'Subtopic', 'Year',
                'Focus_Topic', 'Focus_Subtopic'
            ])

    def load_topics_and_subtopics(self):
        """
        Load topics and subtopics from the topics.csv file.
        """
        if os.path.exists(self.topics_file):
            df_topics = pd.read_csv(self.topics_file)
            topics = df_topics['Topic'].unique().tolist()
            subtopics = {}

            # Populate the subtopics dictionary
            for topic in topics:
                subtopics[topic] = df_topics[df_topics['Topic']
                                             == topic]['Subtopic'].tolist()

            return topics, subtopics
        else:
            return [], {}

    def save_database(self):
        """
        Save the current DataFrame to the CSV file.
        """
        self.df.to_csv(self.db_file, index=False)

    def display_sidebar(self):
        """
        Display the sidebar for adding new questions and custom topics/subtopics.
        """
        st.sidebar.header('Add/Edit Question')

        # Add new question (this comes first)
        st.sidebar.subheader("Add New Question")
        question_id = st.sidebar.text_input('Custom Question ID')
        year = st.sidebar.number_input(
            'Year', min_value=1900, max_value=2100, value=2025)

        # Ensure a blank option is available for topics and subtopics
        topic = st.sidebar.multiselect('Select Topic(s)', [''] + self.topics)
        subtopic_options = [
            sub for t in topic if t in self.subtopics for sub in self.subtopics[t]]
        subtopic = st.sidebar.multiselect(
            'Select Subtopic(s)', [''] + list(set(subtopic_options)))

        focus_topic = st.sidebar.multiselect(
            'Focus Topic(s)', [''] + self.topics)
        focus_subtopic_options = [
            sub for t in focus_topic if t in self.subtopics for sub in self.subtopics[t]]
        focus_subtopic = st.sidebar.multiselect(
            'Focus Subtopic(s)', [''] + list(set(focus_subtopic_options)))

        if st.sidebar.button('Add Question'):
            self.add_question(question_id, topic, subtopic,
                              year, focus_topic, focus_subtopic)

        # Manage Custom Topic and Subtopic (this comes last)
        st.sidebar.subheader("Manage Custom Topics and Subtopics")

        # Add custom topic
        add_custom_topic = st.sidebar.text_input("Add Custom Topic")
        add_custom_subtopic = st.sidebar.text_input(
            "Add Subtopic for Custom Topic")

        # Edit existing custom topics
        custom_topic_to_edit = st.sidebar.selectbox(
            # Shows all topics including custom
            "Edit Custom Topic", [''] + self.topics)
        if custom_topic_to_edit:
            edited_topic_name = st.sidebar.text_input(
                "Edit Topic Name", value=custom_topic_to_edit)
            edited_subtopics = st.sidebar.text_area(
                "Edit Subtopics (comma-separated)",
                value=', '.join(self.subtopics.get(custom_topic_to_edit, []))
            )

            if st.sidebar.button("Save Topic Changes"):
                # Update the custom topic and subtopics
                self.update_custom_topic(
                    custom_topic_to_edit, edited_topic_name, edited_subtopics)

        # Add the custom topic if new
        if add_custom_topic:
            self.add_custom_topic(add_custom_topic, add_custom_subtopic)

    def add_custom_topic(self, custom_topic, custom_subtopic):
        """
        Add a new custom topic and its subtopic if provided.
        """
        if custom_topic not in self.topics:
            self.topics.append(custom_topic)
            self.subtopics[custom_topic] = [
                custom_subtopic] if custom_subtopic else []
            st.sidebar.success("Custom topic added successfully!")
            self.save_topics()  # Save topics to CSV after modification
        else:
            st.sidebar.warning("Topic already exists!")

    def update_custom_topic(self, old_topic, new_topic, new_subtopics):
        """
        Update an existing custom topic and its subtopics.
        """
        new_subtopics_list = [sub.strip()
                              for sub in new_subtopics.split(',') if sub.strip()]

        # Update the topic name
        if old_topic in self.topics:
            self.topics = [new_topic if t ==
                           old_topic else t for t in self.topics]
            self.subtopics[new_topic] = new_subtopics_list

            # Remove old topic
            if old_topic != new_topic:
                del self.subtopics[old_topic]

            st.sidebar.success("Custom topic updated successfully!")
            self.save_topics()  # Save topics to CSV after modification
        else:
            st.sidebar.error("Topic does not exist!")

    def save_topics(self):
        """
        Save the current topics and subtopics to the topics.csv file.
        """
        rows = []
        for topic, subs in self.subtopics.items():
            for sub in subs:
                rows.append([topic, sub])
        df_topics = pd.DataFrame(rows, columns=["Topic", "Subtopic"])
        df_topics.to_csv(self.topics_file, index=False)

    def add_question(self, question_id, topic, subtopic, year, focus_topic, focus_subtopic):
        """
        Add a new question to the database.
        """
        if question_id:
            new_data = {
                'Custom_Question_ID': question_id,
                'Topic': ', '.join(topic),
                'Subtopic': ', '.join(subtopic) if subtopic else '',
                'Year': year,
                'Focus_Topic': ', '.join(focus_topic),
                'Focus_Subtopic': ', '.join(focus_subtopic)
            }
            new_df = pd.DataFrame([new_data])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.save_database()
            st.sidebar.success("Question added successfully!")
        else:
            st.sidebar.error("Question ID cannot be empty!")

    def display_questions(self):
        """
        Display the database and allow editing or deleting questions.
        """
        st.header('Question Database')
        if len(self.df) > 0:
            st.write(self.df)
            self.edit_or_delete_question()
        else:
            st.write("No questions available.")

    def edit_or_delete_question(self):
        """
        Allow editing or deleting a selected question.
        """
        selected_question_id = st.selectbox(
            "Select a question to edit or delete", self.df['Custom_Question_ID'].tolist(
            )
        )
        selected_question = self.df[self.df['Custom_Question_ID']
                                    == selected_question_id]

        if selected_question.empty:
            st.warning("No question selected.")
            return

        st.subheader("Edit Question Details")
        current_topic, current_subtopics, current_focus_topic, current_focus_subtopic = self.get_current_values(
            selected_question
        )

        edit_topics = st.multiselect(
            "Edit Topic(s)", [''] + self.topics, default=current_topic)
        edit_subtopics_options = [
            sub for topic in edit_topics if topic in self.subtopics for sub in self.subtopics.get(topic, [])
        ]
        edit_subtopics = st.multiselect(
            "Edit Subtopic(s)", [
                ''] + list(set(edit_subtopics_options + current_subtopics)),
            default=current_subtopics
        )

        edit_year = st.number_input("Edit Year", value=int(
            selected_question['Year'].values[0]))

        edit_focus_topics = st.multiselect(
            "Edit Focus Topic(s)", [''] + self.topics, default=current_focus_topic)
        edit_focus_subtopics_options = [
            sub for topic in edit_focus_topics if topic in self.subtopics for sub in self.subtopics.get(topic, [])
        ]
        edit_focus_subtopics = st.multiselect(
            "Edit Focus Subtopic(s)", [
                ''] + list(set(edit_focus_subtopics_options + current_focus_subtopic)),
            default=current_focus_subtopic
        )

        if st.button("Save Changes"):
            self.save_changes(selected_question_id, edit_topics, edit_subtopics,
                              edit_year, edit_focus_topics, edit_focus_subtopics)

        if st.button("Delete Question"):
            self.delete_question(selected_question_id)

    def get_current_values(self, question_row):
        """
        Helper function to extract current values from the DataFrame row.
        This ensures that missing values are handled properly by converting them to empty strings.
        """
        topic = str(question_row['Topic'].values[0]) if pd.notna(
            question_row['Topic'].values[0]) else ''
        subtopic = str(question_row['Subtopic'].values[0]) if pd.notna(
            question_row['Subtopic'].values[0]) else ''
        focus_topic = str(question_row['Focus_Topic'].values[0]) if pd.notna(
            question_row['Focus_Topic'].values[0]) else ''
        focus_subtopic = str(question_row['Focus_Subtopic'].values[0]) if pd.notna(
            question_row['Focus_Subtopic'].values[0]) else ''

        # Now split safely, avoiding the issue of NaN
        topic = topic.split(', ') if topic else []
        subtopic = subtopic.split(', ') if subtopic else []
        focus_topic = focus_topic.split(', ') if focus_topic else []
        focus_subtopic = focus_subtopic.split(', ') if focus_subtopic else []

        return topic, subtopic, focus_topic, focus_subtopic

    def save_changes(self, question_id, topic, subtopic, year, focus_topic, focus_subtopic):
        """
        Save the changes made to an existing question.
        """
        self.df.loc[self.df['Custom_Question_ID'] == question_id, [
            'Topic', 'Subtopic', 'Year', 'Focus_Topic', 'Focus_Subtopic']] = [
            ', '.join(topic), ', '.join(subtopic), year, ', '.join(focus_topic), ', '.join(focus_subtopic)]
        self.save_database()
        st.success("Changes saved successfully!")

    def delete_question(self, question_id):
        """
        Delete the selected question from the database.
        """
        self.df = self.df[self.df['Custom_Question_ID'] != question_id]
        self.save_database()
        st.success("Question deleted successfully!")


if __name__ == "__main__":
    app = QuestionDatabaseApp()
    app.display_sidebar()
    app.display_questions()
