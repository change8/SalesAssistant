console.log('register.js loaded');

function toggleSecurityFields() {
    const fields = document.getElementById('securityFields');
    const icon = document.getElementById('securityToggleIcon');
    if (fields.style.display === 'none') {
        fields.style.display = 'block';
        icon.innerText = '▲';
    } else {
        fields.style.display = 'none';
        icon.innerText = '▼';
    }
}

document.getElementById('securityQuestion').addEventListener('change', function () {
    const customGroup = document.getElementById('customQuestionGroup');
    if (this.value === 'custom') {
        customGroup.style.display = 'block';
    } else {
        customGroup.style.display = 'none';
    }
});

document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const phone = document.getElementById('phone').value.trim();
    const fullName = document.getElementById('fullName').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Optional fields
    const email = document.getElementById('email').value.trim();
    let securityQuestion = document.getElementById('securityQuestion').value;
    if (securityQuestion === 'custom') {
        securityQuestion = document.getElementById('customQuestion').value.trim();
    }
    const securityAnswer = document.getElementById('securityAnswer').value.trim();

    // Clear error on input
    document.getElementById('password').addEventListener('input', function () {
        const errorEl = document.getElementById('passwordError');
        errorEl.style.display = 'none';
        this.style.borderColor = '';
    });

    // Validation
    let isValid = true;
    let errorMsg = '';

    if (password.length < 8 || !/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
        isValid = false;
        errorMsg = '密码长度必须至少为 8 位，且包含字母和数字';
    } else if (password !== confirmPassword) {
        isValid = false;
        errorMsg = '两次输入的密码不一致';
    }

    if (!isValid) {
        const errorEl = document.getElementById('passwordError');
        errorEl.textContent = errorMsg;
        errorEl.style.display = 'block';

        // Highlight input
        document.getElementById('password').style.borderColor = 'var(--color-danger)';

        // Shake button
        const btn = e.target.querySelector('button[type="submit"]');
        btn.classList.add('shake');
        setTimeout(() => btn.classList.remove('shake'), 500);

        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerText;
    submitBtn.innerText = '注册中...';
    submitBtn.disabled = true;

    try {
        const payload = {
            phone,
            full_name: fullName,
            password,
            email: email || null,
            security_question: securityQuestion || null,
            security_answer: securityAnswer || null
        };

        await apiCall('/auth/register', 'POST', payload);

        alert('注册成功！请登录。');
        window.location.href = 'login.html';

    } catch (error) {
        console.error('Registration error:', error);
        // Fix [object Object] issue by checking error structure
        let msg = error.message || '注册失败，请重试';
        if (typeof error === 'object' && error.detail) {
            msg = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
        }
        alert(msg);
        submitBtn.innerText = originalText;
        submitBtn.disabled = false;
    }
});
