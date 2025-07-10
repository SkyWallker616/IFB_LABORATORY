document.addEventListener('DOMContentLoaded', () => {
  // FOTO
  const uploadAvatarBtn = document.getElementById('uploadAvatar');
  const avatarInput = document.getElementById('avatarInput');
  const saveAvatarBtn = document.getElementById('saveAvatarBtn');
  const avatarImg = document.getElementById('avatarImg');
  const fotoForm = document.getElementById('fotoForm');

  uploadAvatarBtn.addEventListener('click', () => {
    avatarInput.click();
  });

  avatarInput.addEventListener('change', () => {
    if (avatarInput.files.length > 0) {
      // Mostrar botão salvar
      saveAvatarBtn.classList.remove('d-none');

      // Pré-visualizar imagem local
      const reader = new FileReader();
      reader.onload = e => {
        avatarImg.src = e.target.result;
      };
      reader.readAsDataURL(avatarInput.files[0]);
    }
  });

  // Quando salvar o formulário da foto, o Flask vai receber e processar
  fotoForm.addEventListener('submit', () => {
    // Você pode desabilitar o botão para evitar múltiplos cliques, por exemplo
    saveAvatarBtn.disabled = true;
  });

  // NOME
  const userNameDisplay = document.getElementById('userNameDisplay');
  const userNameInput = document.getElementById('userNameInput');
  const editNameBtn = document.getElementById('editNameBtn');
  const saveNameBtn = document.getElementById('saveNameBtn');
  const cancelNameBtn = document.getElementById('cancelNameBtn');
  const nomeForm = document.getElementById('nomeForm');

  editNameBtn.addEventListener('click', () => {
    userNameInput.classList.remove('d-none');
    userNameDisplay.classList.add('d-none');
    editNameBtn.classList.add('d-none');
    saveNameBtn.classList.remove('d-none');
    cancelNameBtn.classList.remove('d-none');
  });

  cancelNameBtn.addEventListener('click', () => {
    userNameInput.value = userNameDisplay.textContent.trim();
    userNameInput.classList.add('d-none');
    userNameDisplay.classList.remove('d-none');
    editNameBtn.classList.remove('d-none');
    saveNameBtn.classList.add('d-none');
    cancelNameBtn.classList.add('d-none');
  });

  nomeForm.addEventListener('submit', (e) => {
    if(userNameInput.value.trim() === '') {
      e.preventDefault();
      alert('O nome não pode ficar vazio.');
      return false;
    }
    saveNameBtn.disabled = true;
  });
});
