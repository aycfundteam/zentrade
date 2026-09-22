# Bybit competition context and evidence boundary

## What is externally supported

Bybit's official March 2026 material states that:

- the AI vs. Human event ran from March 6 to March 27, 2026;
- AYC Fund was one of six institutional participants;
- the broader retail event exposed AI squad performance on the campaign page.

Sources:

- [Bybit event page](https://www.bybit.com/en/promo/campaign/AI_trading_competition)
- [Bybit guide to the March 6–27 event](https://www.bybit.com/en/learn/bybit-guide/ai-vs-human-crypto-trading-contest)
- [Bybit press release naming AYC Fund](https://www.bybit.com/en/press/post/bybit-expands-cex-s-first-retail-accessible-ai-trading-competition-with-over-360k-in-prizes-bltb87e377bb6fada3a)

## AYC result record

AYC's retained competition record lists the AI division result as **rank #1, +14.82%**. The live leaderboard is dynamic and its final row is not reproduced in this repository, so the README labels this as AYC's competition record rather than presenting the code sample as independent proof.

## Read-only account reconstruction

For the exact window **2026-03-06 03:00 UTC through 2026-03-27 03:00 UTC**, a read-only Bybit V5 reconstruction of the connected account found:

| Item | Value |
|---|---:|
| Closed PnL rows | 170 |
| Trade executions | 682 |
| Funding entries | 58 |
| Sum of closed PnL | +317.39438557 USDT |
| Fees | -59.02082123 USDT |
| Funding | +3.48215909 USDT |
| Net wallet PnL excluding transfers | +316.83743975 USDT |
| In-period transfer in | +1,151.3813 USDT |
| Inferred opening cash balance | 1,090.40552875 USDT |
| Simple realized return on opening cash plus deposit | +14.13325458% |

The reconstruction used cursor exhaustion in seven-day windows across Bybit's closed-PnL, execution, and transaction-log endpoints. The account identifier and raw authenticated responses are deliberately excluded.

The +14.13% reconstruction and +14.82% competition figure use different evidence surfaces. Possible differences include leaderboard snapshots, exact boundary handling, transfer treatment, unrealized PnL, and Bybit's competition formula. They should not be forced into one number.

## Repository boundary

This repository contains a new research implementation and a public OHLCV sample. It does not contain account credentials, authenticated responses, the production engine, or an exact live-account replay.
