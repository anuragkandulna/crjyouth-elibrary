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
import About from "./components/About/About.jsx";
import LibraryCard from "./components/LibraryCard/LibraryCard.jsx";
import { Provider } from "react-redux";
import { store } from "./app/store.js";
import Error404 from "./components/Error404/Error404.jsx";
import Rules from "./components/Rules/Rules.jsx";
import FAQ from "./components/FAQ/FAQ.jsx";
import PrivacyPolicy from "./components/PrivacyPolicy/PrivacyPolicy.jsx";
import Credits from "./components/Credits/Credits.jsx";

// All the public routes down here:
const router = createBrowserRouter(
    createRoutesFromElements(
        <Route path="/" element={<App />}>
            <Route path="" element={<Home />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Registration />} />
            <Route path="books" element={<BookCatalogue />} />
            <Route path="about" element={<About />} />
            <Route path="library-card" element={<LibraryCard />} />
            <Route path="rules" element={<Rules />} />
            <Route path="faq" element={<FAQ />} />
            <Route path="privacy-policy" element={<PrivacyPolicy />} />
            <Route path="credits" element={<Credits />} />
            <Route path="*" element={<Error404 />} />
        </Route>
    )
);

createRoot(document.getElementById("root")).render(
    <Provider store={store}>
        <RouterProvider router={router} />
    </Provider>
);
