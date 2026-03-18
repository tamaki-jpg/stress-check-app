// categories: A (仕事のストレス要因), B (心身のストレス反応), C (周囲のサポート)
export const scoringScale = {
  // A, C categories
  regular: [
    { value: 1, label: 'そうだ' },
    { value: 2, label: 'まあそうだ' },
    { value: 3, label: 'ややちがう' },
    { value: 4, label: 'ちがう' }
  ],
  // B category
  frequency: [
    { value: 1, label: 'ほとんどなかった' },
    { value: 2, label: 'ときどきあった' },
    { value: 3, label: 'しばしばあった' },
    { value: 4, label: 'ほとんどいつもあった' }
  ]
};

// Simplified version of the 57 questions for demonstration purposes
// To keep the initial implementation manageable, we include a representative subset
// A full implementation would contain all 57 items mapped to their exact scales
export const questions = [
  // Category A: 職場のストレス要因 (Causes of stress at work)
  { id: 'A1', category: 'A', text: '非常にたくさんの仕事をしなければならない', type: 'regular', reverse: false },
  { id: 'A2', category: 'A', text: '時間内に仕事が処理しきれない', type: 'regular', reverse: false },
  { id: 'A3', category: 'A', text: '一生懸命働かなければならない', type: 'regular', reverse: false },
  { id: 'A4', category: 'A', text: 'かなり注意を集中する必要がある', type: 'regular', reverse: false },
  { id: 'A5', category: 'A', text: '高度の知識や技術が必要なむずかしい仕事だ', type: 'regular', reverse: false },
  { id: 'A6', category: 'A', text: '自分のペースで仕事ができる', type: 'regular', reverse: true }, // Higher score = more stress (if they can't)
  { id: 'A7', category: 'A', text: '職場の仕事の方針に自分の意見を反映できる', type: 'regular', reverse: true },

  // Category B: 心身のストレス反応 (Physical and mental stress reactions) - Past month
  { id: 'B1', category: 'B', text: '活気がわいてくる', type: 'frequency', reverse: true },
  { id: 'B2', category: 'B', text: '元気がいっぱいだ', type: 'frequency', reverse: true },
  { id: 'B3', category: 'B', text: '生き生きする', type: 'frequency', reverse: true },
  { id: 'B4', category: 'B', text: '怒りを感じる', type: 'frequency', reverse: false },
  { id: 'B5', category: 'B', text: '内心腹立たしい', type: 'frequency', reverse: false },
  { id: 'B6', category: 'B', text: 'イライラしている', type: 'frequency', reverse: false },
  { id: 'B7', category: 'B', text: 'ひどく疲れた', type: 'frequency', reverse: false },
  { id: 'B8', category: 'B', text: 'へとへとだ', type: 'frequency', reverse: false },
  { id: 'B9', category: 'B', text: 'だるい', type: 'frequency', reverse: false },
  { id: 'B10', category: 'B', text: '気が張っている', type: 'frequency', reverse: false },
  { id: 'B11', category: 'B', text: '不安だ', type: 'frequency', reverse: false },
  { id: 'B12', category: 'B', text: '落着かない', type: 'frequency', reverse: false },
  { id: 'B13', category: 'B', text: 'ゆううつだ', type: 'frequency', reverse: false },
  { id: 'B14', category: 'B', text: '何をするのも面倒だ', type: 'frequency', reverse: false },
  { id: 'B15', category: 'B', text: '物事に集中できない', type: 'frequency', reverse: false },

  // Category C: 周囲のサポート (Support from others)
  { id: 'C1', category: 'C', text: '上司はどのくらい気軽に話ができますか', type: 'regular', reverse: true },
  { id: 'C2', category: 'C', text: '上司はあなたが困った時、どのくらい頼りになりますか', type: 'regular', reverse: true },
  { id: 'C3', category: 'C', text: '職場の同僚はどのくらい気軽に話ができますか', type: 'regular', reverse: true },
  { id: 'C4', category: 'C', text: '職場の同僚はあなたが困った時、どのくらい頼りになりますか', type: 'regular', reverse: true }
];

export const categories = {
  A: { title: '職場のストレス要因', description: '仕事の量、質、コントロール度などに関する質問' },
  B: { title: '心身のストレス反応', description: '最近１ヶ月間のあなたの状態についてお答えください' },
  C: { title: '周囲のサポート', description: 'あなたをとりまく環境についてお答えください' }
};
