/* 
    Redux store defined here
*/

import { configureStore } from "@reduxjs/toolkit";
import userReducer from "../features/user/userSlice";
// import projectReducer from "../features/project/projectSlice";

export const store = configureStore({
    // TODO: Add configure store
    reducer: {
        user: userReducer,
        // project: projectReducer,
    },
});
