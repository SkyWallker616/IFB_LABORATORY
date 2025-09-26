// Validação de formulários de autenticação
document.addEventListener('DOMContentLoaded', function() {
    // Validação do formulário de login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username');
            const password = document.getElementById('password');

            if (username.value.trim() === '') {
                e.preventDefault();
                showError(username, 'Por favor, insira seu nome de usuário');
            }

            if (password.value.trim() === '') {
                e.preventDefault();
                showError(password, 'Por favor, insira sua senha');
            }
        });
    }

    // Validação do formulário de registro
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const password2 = document.getElementById('password2');

            if (password.value !== password2.value) {
                e.preventDefault();
                showError(password2, 'As senhas não coincidem');
            }

            if (password.value.length < 8) {
                e.preventDefault();
                showError(password, 'A senha deve ter pelo menos 8 caracteres');
            }
        });

        // Mostrar/ocultar campos baseados no tipo de usuário
        const userTypeRadios = document.querySelectorAll('input[name="tipo"]');
        const alunoFields = document.getElementById('alunoFields');
        const professorFields = document.getElementById('professorFields');

        function toggleFields() {
            const selectedType = document.querySelector('input[name="tipo"]:checked').value;

            if (selectedType === 'aluno') {
                alunoFields.style.display = 'block';
                professorFields.style.display = 'none';
            } else {
                alunoFields.style.display = 'none';
                professorFields.style.display = 'block';
            }
        }

        if (userTypeRadios.length > 0) {
            userTypeRadios.forEach(radio => {
                radio.addEventListener('change', toggleFields);
            });
            toggleFields(); // Chamar inicialmente para configurar o estado correto
        }
    }

    // Função para mostrar erros de validação
    function showError(input, message) {
        const formControl = input.parentElement;
        const errorDiv = formControl.querySelector('.invalid-feedback');

        if (!errorDiv) {
            const div = document.createElement('div');
            div.className = 'invalid-feedback d-block';
            div.textContent = message;
            formControl.appendChild(div);
        } else {
            errorDiv.textContent = message;
        }

        input.classList.add('is-invalid');
        input.focus();
    }
});