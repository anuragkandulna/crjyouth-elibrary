import {
    LIBRARY_NAME,
    LIBRARY_EMAIL,
    LIBRARY_ADDRESS,
} from "../../constants/constants";

export default function PrivacyPolicy() {
    const currentDate = new Date().toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
    });

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Main Content */}
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-lg shadow-sm border p-8">
                    <div className="text-center mb-12">
                        <h2 className="text-4xl font-bold text-gray-900 mb-4">
                            Privacy Policy
                        </h2>
                        <p className="text-lg text-gray-600">
                            Effective Date: {currentDate}
                        </p>
                    </div>

                    <div className="prose prose-lg max-w-none">
                        <p className="text-gray-700 mb-8">
                            Your privacy is important to us. This Privacy Policy
                            explains how {LIBRARY_NAME} ("we," "our," or "us")
                            collects, uses, and protects your personal
                            information when you use our services, website, and
                            digital platforms.
                        </p>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                1. Information We Collect
                            </h3>
                            <p className="text-gray-700 mb-4">
                                We may collect the following types of
                                information when you use our library services:
                            </p>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    <strong>Personal Information:</strong> Name,
                                    email address, phone number, and membership
                                    ID when you register.
                                </li>
                                <li>
                                    <strong>Library Usage Data:</strong>{" "}
                                    Borrowed books, reservations, digital
                                    resource access, and overdue history.
                                </li>
                                <li>
                                    <strong>Technical Data:</strong> Cookies, IP
                                    address, browser type, and device
                                    information when you access our website or
                                    mobile application.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                2. How We Use Your Information
                            </h3>
                            <p className="text-gray-700 mb-4">
                                Your information is used to:
                            </p>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Manage your membership and provide library
                                    services.
                                </li>
                                <li>
                                    Track borrowed, reserved, and returned
                                    items.
                                </li>
                                <li>
                                    Send important updates such as due-date
                                    reminders or policy changes.
                                </li>
                                <li>
                                    Improve our library services and digital
                                    platforms.
                                </li>
                                <li>
                                    Ensure security and prevent misuse of
                                    resources.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                3. Sharing of Information
                            </h3>
                            <p className="text-gray-700 mb-4">
                                We respect your privacy and do not sell or rent
                                your personal information. We may share data
                                only in these cases:
                            </p>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    With service providers (e.g., digital book
                                    platforms) strictly for delivering services.
                                </li>
                                <li>
                                    When required by law, regulation, or legal
                                    process.
                                </li>
                                <li>
                                    To protect the rights, property, or safety
                                    of the Library or its members.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                4. Data Retention
                            </h3>
                            <p className="text-gray-700">
                                We keep your personal information only as long
                                as necessary to provide services, comply with
                                legal obligations, or resolve disputes. Once no
                                longer needed, your data will be securely
                                deleted.
                            </p>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                5. Security
                            </h3>
                            <p className="text-gray-700">
                                We use reasonable technical and organizational
                                measures to protect your data against
                                unauthorized access, loss, or misuse. However,
                                no system is 100% secure, and we cannot
                                guarantee absolute protection.
                            </p>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                6. Your Rights
                            </h3>
                            <p className="text-gray-700 mb-4">
                                As a library member, you have the right to:
                            </p>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Access and review your personal information.
                                </li>
                                <li>Request corrections or updates.</li>
                                <li>
                                    Request deletion of your account and related
                                    data (subject to outstanding dues or
                                    obligations).
                                </li>
                                <li>Opt out of promotional communications.</li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                7. Cookies & Digital Tools
                            </h3>
                            <p className="text-gray-700">
                                Our website may use cookies to enhance your
                                browsing experience. You can control cookie
                                settings in your browser. Some features may not
                                function properly if cookies are disabled.
                            </p>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                8. Changes to This Policy
                            </h3>
                            <p className="text-gray-700">
                                We may update this Privacy Policy from time to
                                time. The latest version will always be
                                available on our website with the effective date
                                noted.
                            </p>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                9. Contact Us
                            </h3>
                            <p className="text-gray-700 mb-4">
                                If you have questions or concerns about this
                                Privacy Policy or your personal data, please
                                contact us at:
                            </p>
                            <div className="bg-gray-50 rounded-lg p-6 space-y-3">
                                <div className="flex items-center">
                                    <span className="text-2xl mr-3">📧</span>
                                    <span className="text-gray-700">
                                        <a
                                            href={`mailto:${LIBRARY_EMAIL}`}
                                            className="text-indigo-600 hover:text-indigo-500 underline"
                                        >
                                            {LIBRARY_EMAIL}
                                        </a>
                                    </span>
                                </div>
                                <div className="flex items-center">
                                    <span className="text-xl mr-3">📍</span>
                                    <span className="text-gray-700">
                                        {LIBRARY_ADDRESS}
                                    </span>
                                </div>
                            </div>
                        </section>
                    </div>

                    {/* Footer */}
                    <div className="mt-12 pt-8 border-t border-gray-200 text-center">
                        <p className="text-gray-500 text-sm">
                            This Privacy Policy is effective as of {currentDate}{" "}
                            and applies to all users of {LIBRARY_NAME} services.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
