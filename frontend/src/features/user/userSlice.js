import { createSlice } from "@reduxjs/toolkit";

const initialState = {
    firstname: "",
    lastname: "",
    user_id: "",
    is_admin: false,
};

export const userSlice = createSlice({
    name: "user",
    initialState,

    // List of all reducers
    reducers: {
        // 1. Authenticate existing user
        loginUser: (state, action) => {
            state.firstname = action.payload.firstname;
            state.lastname = action.payload.lastname;
            state.user_id = action.payload.user_id;
            state.is_admin = action.payload.is_admin;
        },
        // 2. Logout user
        logoutUser: (state) => {
            state.firstname = "";
            state.lastname = "";
            state.user_id = "";
            state.is_admin = false;
        },
    },
});

// Export all reducers individually
export const { loginUser, logoutUser } = userSlice.actions;

// Register the reducer to store
export default userSlice.reducer;
