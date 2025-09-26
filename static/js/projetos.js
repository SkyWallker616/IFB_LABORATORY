document.addEventListener('DOMContentLoaded', function() {
    // Confirmação antes de ações importantes
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja excluir este projeto?')) {
                e.preventDefault();
            }
        });
    });

    // Contador de caracteres para textareas
    const textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.getAttribute('data-max-length'));
        const counterId = textarea.id + '-counter';
        let counter = document.getElementById(counterId);

        if (!counter) {
            counter = document.createElement('div');
            counter.id = counterId;
            counter.className = 'form-text text-end';
            textarea.parentNode.appendChild(counter);
        }

        function updateCounter() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${remaining} caracteres restantes`;
            if (remaining < 0) {
                counter.classList.add('text-danger');
            } else {
                counter.classList.remove('text-danger');
            }
        }

        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });

    // Preview de markdown (se aplicável)
    const markdownTextareas = document.querySelectorAll('textarea[data-markdown-preview]');
    markdownTextareas.forEach(textarea => {
        const previewId = textarea.getAttribute('data-markdown-preview');
        const preview = document.getElementById(previewId);

        if (preview) {
            textarea.addEventListener('input', function() {
                // Simples conversão para demonstração (usar biblioteca como marked.js para implementação real)
                preview.innerHTML = textarea.value
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // negrito
                    .replace(/\*(.*?)\*/g, '<em>$1</em>') // itálico
                    .replace(/\n/g, '<br>'); // quebras de linha
            });
        }
    });
});