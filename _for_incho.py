import streamlit as st
import pandas as pd
import os


class ProblemDatabaseApp:
    def __init__(
        self, db_file="sample_db.csv", categories_file="sample_categories.csv"
    ):
        self.db_file = db_file
        self.categories_file = categories_file
        self.df = self.load_database()
        self.categories, self.subcategories = self.load_categories_and_subcategories()

    def load_database(self):
        """
        Load the problem database from the CSV file or initialize a new DataFrame if it doesn't exist.
        """
        if os.path.exists(self.db_file):
            return pd.read_csv(self.db_file)
        else:
            return pd.DataFrame(
                columns=[
                    "Custom_Problem_ID",
                    "Category",
                    "Subcategory",
                    "Year",
                    "Focus_Category",
                    "Focus_Subcategory",
                ]
            )

    def load_categories_and_subcategories(self):
        """
        Load categories and subcategories from the categories.csv file.
        """
        if os.path.exists(self.categories_file):
            df_categories = pd.read_csv(self.categories_file)
            categories = df_categories["Category"].unique().tolist()
            subcategories = {}

            # Populate the subcategories dictionary
            for category in categories:
                subcategories[category] = df_categories[
                    df_categories["Category"] == category
                ]["Subcategory"].tolist()

            return categories, subcategories
        else:
            return [], {}

    def save_database(self):
        """
        Save the current DataFrame to the CSV file.
        """
        self.df.to_csv(self.db_file, index=False)

    def display_sidebar(self):
        """
        Display the sidebar for adding new problems and custom categories/subcategories.
        """
        st.sidebar.header("Add/Edit Problem")

        # Add new problem (this comes first)
        st.sidebar.subheader("Add New Problem")
        problem_id = st.sidebar.text_input("Custom Problem ID")
        year = st.sidebar.number_input(
            "Year", min_value=1900, max_value=2100, value=2025
        )

        # Ensure a blank option is available for categories and subcategories
        category = st.sidebar.multiselect("Select Category(s)", [""] + self.categories)
        subcategory_options = [
            sub
            for t in category
            if t in self.subcategories
            for sub in self.subcategories[t]
        ]
        subcategory = st.sidebar.multiselect(
            "Select Subcategory(s)", [""] + list(set(subcategory_options))
        )

        focus_category = st.sidebar.multiselect(
            "Focus Category(s)", [""] + self.categories
        )
        focus_subcategory_options = [
            sub
            for t in focus_category
            if t in self.subcategories
            for sub in self.subcategories[t]
        ]
        focus_subcategory = st.sidebar.multiselect(
            "Focus Subcategory(s)", [""] + list(set(focus_subcategory_options))
        )

        if st.sidebar.button("Add Problem"):
            self.add_problem(
                problem_id,
                category,
                subcategory,
                year,
                focus_category,
                focus_subcategory,
            )

        # Manage Custom Category and Subcategory (this comes last)
        st.sidebar.subheader("Manage Custom Categories and Subcategories")

        # Add custom category
        add_custom_category = st.sidebar.text_input("Add Custom Category")
        add_custom_subcategory = st.sidebar.text_input(
            "Add Subcategory for Custom Category"
        )

        # Edit existing custom categories
        custom_category_to_edit = st.sidebar.selectbox(
            # Shows all categories including custom
            "Edit Custom Category",
            [""] + self.categories,
        )
        if custom_category_to_edit:
            edited_category_name = st.sidebar.text_input(
                "Edit Category Name", value=custom_category_to_edit
            )
            edited_subcategories = st.sidebar.text_area(
                "Edit Subcategories (comma-separated)",
                value=", ".join(self.subcategories.get(custom_category_to_edit, [])),
            )

            if st.sidebar.button("Save Category Changes"):
                # Update the custom category and subcategories
                self.update_custom_category(
                    custom_category_to_edit, edited_category_name, edited_subcategories
                )

        # Add the custom category if new
        if add_custom_category:
            self.add_custom_category(add_custom_category, add_custom_subcategory)

    def add_custom_category(self, custom_category, custom_subcategory):
        """
        Add a new custom category and its subcategory if provided.
        """
        if custom_category not in self.categories:
            self.categories.append(custom_category)
            self.subcategories[custom_category] = (
                [custom_subcategory] if custom_subcategory else []
            )
            st.sidebar.success("Custom category added successfully!")
            self.save_categories()  # Save categories to CSV after modification
        else:
            st.sidebar.warning("Category already exists!")

    def update_custom_category(self, old_category, new_category, new_subcategories):
        """
        Update an existing custom category and its subcategories.
        """
        new_subcategories_list = [
            sub.strip() for sub in new_subcategories.split(",") if sub.strip()
        ]

        # Update the category name
        if old_category in self.categories:
            self.categories = [
                new_category if t == old_category else t for t in self.categories
            ]
            self.subcategories[new_category] = new_subcategories_list

            # Remove old category
            if old_category != new_category:
                del self.subcategories[old_category]

            st.sidebar.success("Custom category updated successfully!")
            self.save_categories()  # Save categories to CSV after modification
        else:
            st.sidebar.error("Category does not exist!")

    def save_categories(self):
        """
        Save the current categories and subcategories to the categories.csv file.
        """
        rows = []
        for category, subs in self.subcategories.items():
            for sub in subs:
                rows.append([category, sub])
        df_categories = pd.DataFrame(rows, columns=["Category", "Subcategory"])
        df_categories.to_csv(self.categories_file, index=False)

    def add_problem(
        self, problem_id, category, subcategory, year, focus_category, focus_subcategory
    ):
        """
        Add a new problem to the database.
        """
        if problem_id:
            new_data = {
                "Custom_Problem_ID": problem_id,
                "Category": ", ".join(category),
                "Subcategory": ", ".join(subcategory) if subcategory else "",
                "Year": year,
                "Focus_Category": ", ".join(focus_category),
                "Focus_Subcategory": ", ".join(focus_subcategory),
            }
            new_df = pd.DataFrame([new_data])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.save_database()
            st.sidebar.success("Problem added successfully!")
        else:
            st.sidebar.error("Problem ID cannot be empty!")

    def display_problems(self):
        """
        Display the database and allow editing or deleting problems.
        """
        st.header("Problem Database")
        if len(self.df) > 0:
            st.write(self.df)
            self.edit_or_delete_problem()
        else:
            st.write("No problems available.")

    def edit_or_delete_problem(self):
        """
        Allow editing or deleting a selected problem.
        """
        selected_problem_id = st.selectbox(
            "Select a problem to edit or delete", self.df["Custom_Problem_ID"].tolist()
        )
        selected_problem = self.df[self.df["Custom_Problem_ID"] == selected_problem_id]

        if selected_problem.empty:
            st.warning("No problem selected.")
            return

        st.subheader("Edit Problem Details")
        (
            current_category,
            current_subcategories,
            current_focus_category,
            current_focus_subcategory,
        ) = self.get_current_values(selected_problem)

        edit_categories = st.multiselect(
            "Edit Category(s)", [""] + self.categories, default=current_category
        )
        edit_subcategories_options = [
            sub
            for category in edit_categories
            if category in self.subcategories
            for sub in self.subcategories.get(category, [])
        ]
        edit_subcategories = st.multiselect(
            "Edit Subcategory(s)",
            [""] + list(set(edit_subcategories_options + current_subcategories)),
            default=current_subcategories,
        )

        edit_year = st.number_input(
            "Edit Year", value=int(selected_problem["Year"].values[0])
        )

        edit_focus_categories = st.multiselect(
            "Edit Focus Category(s)",
            [""] + self.categories,
            default=current_focus_category,
        )
        edit_focus_subcategories_options = [
            sub
            for category in edit_focus_categories
            if category in self.subcategories
            for sub in self.subcategories.get(category, [])
        ]
        edit_focus_subcategories = st.multiselect(
            "Edit Focus Subcategory(s)",
            [""]
            + list(set(edit_focus_subcategories_options + current_focus_subcategory)),
            default=current_focus_subcategory,
        )

        if st.button("Save Changes"):
            self.save_changes(
                selected_problem_id,
                edit_categories,
                edit_subcategories,
                edit_year,
                edit_focus_categories,
                edit_focus_subcategories,
            )

        if st.button("Delete Problem"):
            self.delete_problem(selected_problem_id)

    def get_current_values(self, problem_row):
        """
        Helper function to extract current values from the DataFrame row.
        This ensures that missing values are handled properly by converting them to empty strings.
        """
        category = (
            str(problem_row["Category"].values[0])
            if pd.notna(problem_row["Category"].values[0])
            else ""
        )
        subcategory = (
            str(problem_row["Subcategory"].values[0])
            if pd.notna(problem_row["Subcategory"].values[0])
            else ""
        )
        focus_category = (
            str(problem_row["Focus_Category"].values[0])
            if pd.notna(problem_row["Focus_Category"].values[0])
            else ""
        )
        focus_subcategory = (
            str(problem_row["Focus_Subcategory"].values[0])
            if pd.notna(problem_row["Focus_Subcategory"].values[0])
            else ""
        )

        # Now split safely, avoiding the issue of NaN
        category = category.split(", ") if category else []
        subcategory = subcategory.split(", ") if subcategory else []
        focus_category = focus_category.split(", ") if focus_category else []
        focus_subcategory = focus_subcategory.split(", ") if focus_subcategory else []

        return category, subcategory, focus_category, focus_subcategory

    def save_changes(
        self, problem_id, category, subcategory, year, focus_category, focus_subcategory
    ):
        """
        Save the changes made to an existing problem.
        """
        self.df.loc[
            self.df["Custom_Problem_ID"] == problem_id,
            ["Category", "Subcategory", "Year", "Focus_Category", "Focus_Subcategory"],
        ] = [
            ", ".join(category),
            ", ".join(subcategory),
            year,
            ", ".join(focus_category),
            ", ".join(focus_subcategory),
        ]
        self.save_database()
        st.success("Changes saved successfully!")

    def delete_problem(self, problem_id):
        """
        Delete the selected problem from the database.
        """
        self.df = self.df[self.df["Custom_Problem_ID"] != problem_id]
        self.save_database()
        st.success("Problem deleted successfully!")


if __name__ == "__main__":
    app = ProblemDatabaseApp(
        db_file="db/incho_db.csv", categories_file="categories/incho_categories.csv"
    )
    app.display_sidebar()
    app.display_problems()

# """
# ? PROBLEM ID = YYYY_PXX ==> YYYY:YEAR & P:PROBLEM & XX:PROBLEM NUMBER
# * (e.g. 2008_P1 => Problem 1 of year 2008)
# """
