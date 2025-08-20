const faqs = [
    {
        id: 1,
        question: "How do I become a member of the library?",
        answer: "You can register online through our website or visit the library front desk with a valid ID. Once registered, you’ll receive your library ID to borrow books and access digital resources.",
    },
    {
        id: 2,
        question: "Is there a membership fee?",
        answer: "Basic membership is free for all youth and community members. Some premium services, such as special events or extended borrowing, may have a small fee.",
    },
    {
        id: 3,
        question: "How many books can I borrow at a time?",
        answer: "Members can borrow up to 5 books at a time for a 14-day period. Renewals can be requested online unless the book is on hold for another member.",
    },
    {
        id: 4,
        question: "Does the library have digital or e-books?",
        answer: "Yes! We offer a wide collection of e-books, audiobooks, and online resources accessible through our digital library portal.",
    },
    {
        id: 5,
        question: "Can I reserve a book online?",
        answer: "Absolutely. You can log into your account, search for the book, and place a hold. We’ll notify you when it’s available for pickup.",
    },
    {
        id: 6,
        question: "Does the library provide spaces for study or group work?",
        answer: "Yes, we have dedicated quiet study areas as well as group study rooms. You can book group spaces in advance through our website.",
    },
    {
        id: 7,
        question: "What happens if I lose or damage a book?",
        answer: "In case of loss or damage, members are responsible for replacing the book or paying the replacement cost. Please contact the help desk for assistance.",
    },
];

export default function FAQ() {
    return (
        <div className="bg-white">
            <div className="mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8 lg:py-40">
                <h2 className="text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
                    Frequently asked questions
                </h2>
                <dl className="mt-20 divide-y divide-gray-900/10">
                    {faqs.map((faq) => (
                        <div
                            key={faq.id}
                            className="py-8 first:pt-0 last:pb-0 lg:grid lg:grid-cols-12 lg:gap-8"
                        >
                            <dt className="text-base/7 font-semibold text-gray-900 lg:col-span-5">
                                {faq.question}
                            </dt>
                            <dd className="mt-4 lg:col-span-7 lg:mt-0">
                                <p className="text-base/7 text-gray-600">
                                    {faq.answer}
                                </p>
                            </dd>
                        </div>
                    ))}
                </dl>
            </div>
        </div>
    );
}
