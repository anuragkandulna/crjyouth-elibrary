import {
    LIBRARY_NAME,
    LIBRARY_EMAIL,
    LIBRARY_ADDRESS,
} from "../../constants/constants";

export default function Rules() {
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Main Content */}
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-lg shadow-sm border p-8">
                    <div className="text-center mb-12">
                        <h2 className="text-4xl font-bold text-gray-900 mb-4">
                            Library Rules & Guidelines
                        </h2>
                        <p className="text-lg text-gray-600">
                            Please read and follow these rules to ensure a
                            pleasant experience for all members
                        </p>
                    </div>

                    <div className="prose prose-lg max-w-none">
                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                1. Membership & Access
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    A valid library membership card or ID is
                                    required to borrow books or use digital
                                    resources.
                                </li>
                                <li>
                                    Members are responsible for the proper use
                                    of their accounts and borrowed materials.
                                </li>
                                <li>
                                    Lost membership cards should be reported
                                    immediately to avoid misuse.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                2. Borrowing & Returning
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Each member may borrow up to{" "}
                                    <strong>5 books</strong> at a time.
                                </li>
                                <li>
                                    Loan period is <strong>14 days</strong>,
                                    with the option to renew if no one else has
                                    reserved the book.
                                </li>
                                <li>
                                    Overdue items may result in late fees or
                                    suspension of borrowing privileges.
                                </li>
                                <li>
                                    Lost or damaged books must be replaced or
                                    compensated by the member.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                3. Library Conduct
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Respect fellow members and staff at all
                                    times.
                                </li>
                                <li>
                                    Maintain silence in reading and study areas.
                                </li>
                                <li>
                                    Use mobile phones in silent mode; calls
                                    should be taken outside.
                                </li>
                                <li>
                                    Food and drinks (except water) are not
                                    allowed inside the library.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                4. Digital & Online Use
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Digital resources (e-books, audiobooks,
                                    databases) are for personal learning and
                                    research only.
                                </li>
                                <li>
                                    Sharing login credentials with others is
                                    strictly prohibited.
                                </li>
                                <li>
                                    Any misuse of digital platforms may result
                                    in suspension of library access.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                5. Study Spaces & Facilities
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Study rooms must be booked in advance,
                                    subject to availability.
                                </li>
                                <li>
                                    Keep furniture, equipment, and spaces clean
                                    and undamaged.
                                </li>
                                <li>
                                    Sleeping in reading areas is discouraged.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                6. Safety & Security
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Bags may be subject to inspection at entry
                                    or exit points.
                                </li>
                                <li>
                                    Keep personal belongings safe; the library
                                    is not responsible for lost items.
                                </li>
                                <li>
                                    Follow staff instructions during emergencies
                                    or safety drills.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                7. Events & Activities
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Members are welcome to participate in
                                    library-hosted workshops, reading clubs, and
                                    events.
                                </li>
                                <li>
                                    Respect event timings and guidelines set by
                                    organizers.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                8. Disciplinary Action
                            </h3>
                            <ul className="list-disc pl-6 text-gray-700 space-y-2">
                                <li>
                                    Violation of rules may lead to warnings,
                                    fines, suspension, or termination of
                                    membership.
                                </li>
                                <li>
                                    Serious misconduct may result in legal
                                    action where applicable.
                                </li>
                            </ul>
                        </section>

                        <hr className="my-8 border-gray-300" />

                        <section className="mb-8">
                            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                                9. General Reminder
                            </h3>
                            <div className="bg-blue-50 border-l-4 border-blue-400 p-6">
                                <p className="text-gray-700 text-lg italic">
                                    The Library is a community space for
                                    reading, learning, and growth. Please help
                                    us maintain an environment that benefits
                                    everyone.
                                </p>
                            </div>
                        </section>
                    </div>

                    {/* Contact Information */}
                    <div className="mt-12 pt-8 border-t border-gray-200">
                        <div className="text-center">
                            <h4 className="text-lg font-semibold text-gray-900 mb-4">
                                Questions About These Rules?
                            </h4>
                            <p className="text-gray-600 mb-4">
                                If you have any questions or need clarification
                                about these rules, please contact us:
                            </p>
                            <div className="bg-gray-50 rounded-lg p-6 inline-block">
                                <div className="flex items-center mb-3">
                                    <span className="text-xl mr-3">📧</span>
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
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="mt-8 text-center">
                        <p className="text-gray-500 text-sm">
                            These rules are designed to ensure a safe,
                            respectful, and productive environment for all{" "}
                            {LIBRARY_NAME} members.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
