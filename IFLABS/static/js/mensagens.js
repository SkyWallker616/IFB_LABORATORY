// Funcionalidades para o sistema de mensagens
document.addEventListener('DOMContentLoaded', function() {
    // Envio de mensagens via AJAX
    const messageForms = document.querySelectorAll('.message-form');
    messageForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Adiciona a nova mensagem ao chat
                    const messagesContainer = document.querySelector('.messages-container');
                    if (messagesContainer) {
                        const messageElement = document.createElement('div');
                        messageElement.className = 'message outgoing';
                        messageElement.innerHTML = `
                            <div class="message-content">
                                <p>${data.message.corpo}</p>
                                <small class="message-time">Agora</small>
                            </div>
                        `;
                        messagesContainer.appendChild(messageElement);
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }

                    // Limpa o formulário
                    this.reset();
                } else {
                    alert(data.error || 'Erro ao enviar mensagem');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Erro ao enviar mensagem');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            });
        });
    });

    // Atualização automática de mensagens
    function pollMessages() {
        const conversationId = document.getElementById('conversationId')?.value;
        if (!conversationId) return;

        const lastMessageId = document.querySelector('.message:last-child')?.dataset.id || 0;

        fetch(`/mensagens/novas/${conversationId}?ultima=${lastMessageId}`)
            .then(response => response.json())
            .then(messages => {
                if (messages.length > 0) {
                    const messagesContainer = document.querySelector('.messages-container');

                    messages.forEach(msg => {
                        const messageElement = document.createElement('div');
                        messageElement.className = `message ${msg.remetente_id == currentUserId ? 'outgoing' : 'incoming'}`;
                        messageElement.dataset.id = msg.id;
                        messageElement.innerHTML = `
                            <div class="message-content">
                                <p>${msg.corpo}</p>
                                <small class="message-time">${new Date(msg.timestamp).toLocaleTimeString()}</small>
                            </div>
                        `;
                        messagesContainer.appendChild(messageElement);
                    });

                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
            })
            .finally(() => {
                setTimeout(pollMessages, 5000); // Poll a cada 5 segundos
            });
    }

    // Inicia o polling se estiver em uma página de conversa
    if (document.getElementById('conversationId')) {
        setTimeout(pollMessages, 5000);
    }

    // Marcar mensagens como lidas
    const unreadMessages = document.querySelectorAll('.message.unread');
    unreadMessages.forEach(msg => {
        const msgId = msg.dataset.id;
        fetch(`/mensagens/marcar-lida/${msgId}`, { method: 'POST' })
            .then(() => msg.classList.remove('unread'));
    });
});