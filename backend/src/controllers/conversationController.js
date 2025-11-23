const db = require('../config/db');

// Create a new conversation
exports.createConversation = async (req, res) => {
    const { title } = req.body;
    const userId = req.user.id;

    try {
        const result = await db.query(
            'INSERT INTO conversations (user_id, title) VALUES ($1, $2) RETURNING *',
            [userId, title || 'New Chat']
        );
        res.json(result.rows[0]);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
    }
};

// Get all conversations for a user
exports.getConversations = async (req, res) => {
    const userId = req.user.id;

    try {
        const result = await db.query(
            'SELECT * FROM conversations WHERE user_id = $1 ORDER BY updated_at DESC',
            [userId]
        );
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
    }
};

// Get a specific conversation with messages
exports.getConversation = async (req, res) => {
    const { id } = req.params;
    const userId = req.user.id;

    try {
        // Verify ownership
        const conversation = await db.query(
            'SELECT * FROM conversations WHERE id = $1 AND user_id = $2',
            [id, userId]
        );

        if (conversation.rows.length === 0) {
            return res.status(404).json({ error: 'Conversation not found' });
        }

        // Fetch messages
        const messages = await db.query(
            'SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at ASC',
            [id]
        );

        res.json({
            conversation: conversation.rows[0],
            messages: messages.rows
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
    }
};
