import "dotenv/config";

const apiKey = process.env.AGNES_API_KEY;
const baseUrl = process.env.AGNES_BASE_URL || "https://apihub.agnes-ai.com/v1";
const model = process.env.AGNES_MODEL || "agnes-2.5-flash";

const res = await fetch(`${baseUrl}/chat/completions`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${apiKey}`,
  },
  body: JSON.stringify({
    model,
    messages: [{ role: "user", content: "用一句话解释：为什么门禁比聪明更重要？" }],
    max_tokens: 500,
  }),
});

const data = await res.json();
const msg = data.choices?.[0]?.message;

console.log("=== 回答 ===");
console.log(msg?.content?.trim());
console.log("\n=== 思维链 ===");
console.log(msg?.reasoning_content?.trim());