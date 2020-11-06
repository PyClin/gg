# Guntur Gazelle


[![gg-logo.png](https://i.postimg.cc/dtq5zH9r/gg-logo.png)](https://postimg.cc/0rBGSCFy)


> "Every morning in Africa, a gazelle wakes up. It knows it must run faster than the fastest lion or it will be killed. Every morning a lion wakes up. It knows it must outrun the slowest gazelle or it will starve to death. It doesn't matter whether you're a lion or gazelle. When the sun comes up, you'd better be running." - Steve Grasso of Stuart Frankel

Enabling Offline-Offline Payments for traveling anywhere in India for the masses. Completely contactless and cashless.

GG is the blockchain component for the same.


## Why tho?

Japan recently tried  [paying everyone in Japan to travel during the pandemic](https://www.youtube.com/watch?v=oPM55njpHh0). We want to do a similar test run on Indian soil, but add our own spin to it. It'd be a Post COVID-19 stimulus offer from government which will encourage pubic to travel anywhere in India.

It could power any sorts of travel where you usually spend rupee. Just here you'd spend the `INRx`, rupee tokens.

We also extended the same thing which can be used as a travel platform for employee travel claims regarding official work. Employess can travel anywhere in India and can claim their amount whenever they feel like.

## Travel like where?

* Trams for Kolkata people.
* Ferry for Alappuzha people.
* Metro Trains for Delhi people.
* SubUrban Trains for Chennai people.
* KSRTC Bus for Bengaluru people.
* Mofussil Trains for Indian people in general.

these are just few examples.


## Key Stellar Features


It proudly runs on top of [Stellar](https://www.stellar.org/?locale=en). Built for [Stellar Meridian Hackathon 2020](https://meridianhackathon.devpost.com/). You can read more about stellar over [here](https://www.stellar.org/learn/intro-to-stellar?locale=en)

It is based on the new Rupee token we'd be issuing as an asset on stellar (hypothetically, it is still on Horizon's [testnet](https://developers.stellar.org/docs/glossary/testnet/))

It is called `INRx`, a rupee token.

**Stellar Blockchain features we are using**:

*  [Fee bumps](https://developers.stellar.org/docs/glossary/fee-bumps/), which allow an account to cover another account's transaction fees. We use it because everyone likes transaction-fee free transactions. xD. 

* [Sponsored reserves](https://developers.stellar.org/docs/glossary/sponsored-reserves/), which allow an account to cover lumen reserves for another account. We use it for creating new accounts with a small lumen minimum balance from sponsored account.

* [Claimable balances](https://developers.stellar.org/docs/glossary/claimable-balance/), which allow an account to create a balance of any asset, and to designate another account to claim it. We use it for employees claiming their travel expenses from their employer in a hassle-free fashion.

## API documentation

Postman Documentation for the microservice is publically available [here](https://documenter.getpostman.com/view/1756856/TVeiBpiD).

## P.S

This project wouldn't exist without [Stellar Laboratory](https://laboratory.stellar.org/#). It's ease of use is what made this project achievable. Along with their community [Python SDK](https://github.com/StellarCN/py-stellar-base), that `TransactionBuider` API, and their [examples](https://github.com/StellarCN/py-stellar-base/tree/master/examples) directory helped me a lot. Also the awesome people on their discord !!.
