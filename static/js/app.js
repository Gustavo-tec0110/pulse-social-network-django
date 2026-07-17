document.querySelectorAll('[data-character-counter="post"]').forEach((field) => {
  const output = document.querySelector('[data-counter-output]');
  const update = () => {
    const remaining = 280 - field.value.length;
    output.textContent = remaining;
    output.classList.toggle('warning', remaining < 30);
  };
  field.addEventListener('input', update);
  update();
});

document.querySelectorAll('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});
