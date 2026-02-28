export interface Trade {
  id: string;
  activity_type: string;
  symbol: string;
  side: string;
  qty: string;
  price: string;
  cum_qty: string;
  order_id: string;
  transaction_time: string;
  type: string;
}

/**
 * Mock backtest trades for SMA Crossover strategy on SPY.
 * 6 round-trip trades (12 fills): 3 winners, 3 losers.
 * Period: 2024-01-15 to 2025-01-15
 * Starting capital: ~$10,000
 * Average trade return: +1.54%
 */
export const MOCK_TRADES: Trade[] = [
  // --- Trade 1: WIN  Buy $468.30 → Sell $479.15 (+2.32%) ---
  {
    id: "a1b2c3d4-1111-4aaa-b111-000000000001",
    activity_type: "FILL",
    symbol: "SPY",
    side: "buy",
    qty: "21",
    price: "468.30",
    cum_qty: "21",
    order_id: "ord-11111111-aaaa-4bbb-8ccc-111111111111",
    transaction_time: "2024-01-22T15:32:17.482Z",
    type: "fill",
  },
  {
    id: "a1b2c3d4-1111-4aaa-b111-000000000002",
    activity_type: "FILL",
    symbol: "SPY",
    side: "sell",
    qty: "21",
    price: "479.15",
    cum_qty: "21",
    order_id: "ord-11111111-aaaa-4bbb-8ccc-222222222222",
    transaction_time: "2024-02-14T16:45:03.119Z",
    type: "fill",
  },

  // --- Trade 2: LOSS  Buy $491.50 → Sell $485.20 (-1.28%) ---
  {
    id: "a1b2c3d4-2222-4aaa-b222-000000000003",
    activity_type: "FILL",
    symbol: "SPY",
    side: "buy",
    qty: "20",
    price: "491.50",
    cum_qty: "20",
    order_id: "ord-22222222-aaaa-4bbb-8ccc-333333333333",
    transaction_time: "2024-03-11T14:18:42.753Z",
    type: "fill",
  },
  {
    id: "a1b2c3d4-2222-4aaa-b222-000000000004",
    activity_type: "FILL",
    symbol: "SPY",
    side: "sell",
    qty: "20",
    price: "485.20",
    cum_qty: "20",
    order_id: "ord-22222222-aaaa-4bbb-8ccc-444444444444",
    transaction_time: "2024-03-28T17:02:58.301Z",
    type: "fill",
  },

  // --- Trade 3: WIN  Buy $498.75 → Sell $511.40 (+2.54%) ---
  {
    id: "a1b2c3d4-3333-4aaa-b333-000000000005",
    activity_type: "FILL",
    symbol: "SPY",
    side: "buy",
    qty: "20",
    price: "498.75",
    cum_qty: "20",
    order_id: "ord-33333333-aaaa-4bbb-8ccc-555555555555",
    transaction_time: "2024-05-06T15:55:14.628Z",
    type: "fill",
  },
  {
    id: "a1b2c3d4-3333-4aaa-b333-000000000006",
    activity_type: "FILL",
    symbol: "SPY",
    side: "sell",
    qty: "20",
    price: "511.40",
    cum_qty: "20",
    order_id: "ord-33333333-aaaa-4bbb-8ccc-666666666666",
    transaction_time: "2024-06-03T18:21:37.492Z",
    type: "fill",
  },

  // --- Trade 4: LOSS  Buy $514.60 → Sell $507.85 (-1.31%) ---
  {
    id: "a1b2c3d4-4444-4aaa-b444-000000000007",
    activity_type: "FILL",
    symbol: "SPY",
    side: "buy",
    qty: "19",
    price: "514.60",
    cum_qty: "19",
    order_id: "ord-44444444-aaaa-4bbb-8ccc-777777777777",
    transaction_time: "2024-07-15T14:47:23.185Z",
    type: "fill",
  },
  {
    id: "a1b2c3d4-4444-4aaa-b444-000000000008",
    activity_type: "FILL",
    symbol: "SPY",
    side: "sell",
    qty: "19",
    price: "507.85",
    cum_qty: "19",
    order_id: "ord-44444444-aaaa-4bbb-8ccc-888888888888",
    transaction_time: "2024-07-31T19:33:09.847Z",
    type: "fill",
  },

  // --- Trade 5: WIN  Buy $502.10 → Sell $517.90 (+3.15%) ---
  {
    id: "a1b2c3d4-5555-4aaa-b555-000000000009",
    activity_type: "FILL",
    symbol: "SPY",
    side: "buy",
    qty: "19",
    price: "502.10",
    cum_qty: "19",
    order_id: "ord-55555555-aaaa-4bbb-8ccc-999999999999",
    transaction_time: "2024-09-09T16:12:51.334Z",
    type: "fill",
  },
  {
    id: "a1b2c3d4-5555-4aaa-b555-000000000010",
    activity_type: "FILL",
    symbol: "SPY",
    side: "sell",
    qty: "19",
    price: "517.90",
    cum_qty: "19",
    order_id: "ord-55555555-aaaa-4bbb-8ccc-aaaaaaaaaaaa",
    transaction_time: "2024-10-14T17:58:44.716Z",
    type: "fill",
  },

  // --- Trade 6: LOSS  Buy $519.25 → Sell $514.40 (-0.93%) ---
  {
    id: "a1b2c3d4-6666-4aaa-b666-000000000011",
    activity_type: "FILL",
    symbol: "SPY",
    side: "buy",
    qty: "19",
    price: "519.25",
    cum_qty: "19",
    order_id: "ord-66666666-aaaa-4bbb-8ccc-bbbbbbbbbbbb",
    transaction_time: "2024-11-18T15:08:32.201Z",
    type: "fill",
  },
  {
    id: "a1b2c3d4-6666-4aaa-b666-000000000012",
    activity_type: "FILL",
    symbol: "SPY",
    side: "sell",
    qty: "19",
    price: "514.40",
    cum_qty: "19",
    order_id: "ord-66666666-aaaa-4bbb-8ccc-cccccccccccc",
    transaction_time: "2024-12-09T18:41:19.573Z",
    type: "fill",
  },
];
