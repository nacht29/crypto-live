import { NextResponse } from 'next/server';
import { QueryCommand } from '@aws-sdk/lib-dynamodb';
import { getDynamoClient } from '../../../lib/aws';
import { PriceRowSchema, PricesApiResponseSchema } from '../../../lib/types';

export const runtime = 'nodejs'; // required for AWS SDK in Vercel
export const dynamic = 'force-dynamic';

const tableName = process.env.DYNAMO_TABLE_NAME || 'crypto-live-miniticker';
const streamsEnv = process.env.UI_STREAMS || '';

const streamKeys = streamsEnv
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

// fallback: still allow one generic stream to avoid 500s if not configured
const defaultStreamKeys = streamKeys.length ? streamKeys : ['btcusdt@miniTicker'];

export async function GET() {
  try {
    const client = getDynamoClient();

    const results = await Promise.all(
      defaultStreamKeys.map(async (stream) => {
        const command = new QueryCommand({
          TableName: tableName,
          KeyConditionExpression: '#pk = :stream',
          ExpressionAttributeNames: {
            '#pk': 'stream_type',
          },
          ExpressionAttributeValues: {
            ':stream': stream,
          },
          Limit: 1,
          ScanIndexForward: false, // latest first
        });

        const { Items = [] } = await client.send(command);
        const item = Items[0];
        if (!item) return null;

        const priceNum = Number(item.close_price);
        return PriceRowSchema.parse({
          symbol: item.symbol,
          assetName: (item.symbol ?? '').replace(/USDT$/i, '').toUpperCase(),
          price: priceNum,
          delta1h: 0,
          delta24h: 0,
          delta7d: 0,
          marketCap: Number(item.total_traded_volume ?? 0),
          volume24h: Number(item.total_traded_base_asset_volume ?? 0),
        });
      })
    );

    const unique = results.filter(Boolean);

    const response = PricesApiResponseSchema.parse({
      items: unique,
      asOf: new Date().toISOString(),
    });

    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    console.error('Failed to load prices', error);
    return NextResponse.json({ message: 'Failed to load prices' }, { status: 500 });
  }
}
