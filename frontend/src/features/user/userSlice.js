import { createSlice } from "@reduxjs/toolkit";

const initialState = {
    firstname: "myfirstname",
    lastname: "mylastname",
    email: "example@example.com",
    token: "",
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
            state.email = action.payload.email;
            state.token = action.payload.token;
        },
    },
});

// Export all reducers individually
export const { loginUser } = userSlice.actions;

// Register the reducer to store
export default userSlice.reducer;
