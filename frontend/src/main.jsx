import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import {
    Route,
    RouterProvider,
    createBrowserRouter,
    createRoutesFromElements,
} from "react-router-dom";
import "./index.css";
import App from "./App.jsx";
import Home from "./components/Home/Home.jsx";
import Registration from "./components/Registration/Registration.jsx";
import Login from "./components/Login/Login.jsx";
import BookCatalogue from "./components/BookCatalogue/BookCatalogue.jsx";
import AudioBooks from "./components/AudioBooks/AudioBooks.jsx";
import BookDetails from "./components/BookDetails/BookDetails.jsx";
import { Provider } from "react-redux";
import { store } from "./app/store.js";
import Error404 from "./components/Error404/Error404.jsx";

// All the public routes down here:
const router = createBrowserRouter(
    createRoutesFromElements(
        <Route path="/" element={<App />}>
            <Route path="" element={<Home />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Registration />} />
            <Route path="books" element={<BookCatalogue />} />
            <Route path="audiobooks" element={<AudioBooks />} />
            <Route path="bookdetails" element={<BookDetails />} />

            <Route path="*" element={<Error404 />} />
        </Route>
    )
);

createRoot(document.getElementById("root")).render(
    <StrictMode>
        <Provider store={store}>
            <RouterProvider router={router} />
        </Provider>
        {/* <RouterProvider router={router} /> */}
    </StrictMode>
);
