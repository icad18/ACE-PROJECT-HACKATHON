import Head from 'next/head';

export default function Home() {
  return (
    <>
      <Head>
        <title>Marketplace Home</title>
        <meta name="description" content="Welcome to our marketplace" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="flex min-h-screen flex-col items-center justify-center p-24">
        <h1 className="text-5xl font-bold mb-8">
          Welcome to the Marketplace!
        </h1>

        <p className="text-xl mb-12">
          Start exploring products or become a seller today.
        </p>

        <div className="flex space-x-4">
          <a
            href="/products"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700 transition duration-300"
          >
            Browse Products
          </a>
          <a
            href="/auth/register"
            className="px-6 py-3 border border-blue-600 text-blue-600 rounded-lg shadow-md hover:bg-blue-50 transition duration-300"
          >
            Become a Seller
          </a>
        </div>
      </main>
    </>
  );
}
