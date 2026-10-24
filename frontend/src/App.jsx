import { useState } from 'react'

import {

  Routes,

  Route,

  Link,

  Navigate,

  useNavigate,

  useSearchParams,

} from 'react-router-dom'



import { apiRequest } from './services/api'

import Catalogo from './components/Catalogo'

import Carrinho from './components/Carrinho'

import './App.css'



// ============================================

// LOGIN

// ============================================



function Login() {

  const navigate = useNavigate()



  const [email, setEmail] = useState('')

  const [senha, setSenha] = useState('')

  const [erro, setErro] = useState('')

  const [mensagem, setMensagem] = useState('')

  const [carregando, setCarregando] = useState(false)



  async function handleLogin(event) {

    event.preventDefault()

    setErro('')

    setMensagem('')

    setCarregando(true)



    try {

      const data = await apiRequest('/usuarios/login', {

        method: 'POST',

        body: JSON.stringify({ email, senha }),

      })



      if (!data.access_token) {

        throw new Error('A API não retornou um token de acesso.')

      }



      sessionStorage.setItem('access_token', data.access_token)



      navigate('/minha-conta', { replace: true })

    } catch (error) {

      setErro(error.message || 'Não foi possível entrar. Confira seus dados.')

    } finally {

      setCarregando(false)

    }

  }



  return (

    <main className="store">

      <header className="navbar">

        <Link className="logo" to="/">

          e<span>commerce</span>

        </Link>

        <Link className="back-link" to="/">

          Voltar à loja

        </Link>

      </header>



      <section className="login-page">

        <div className="login-decoration">

          <span className="eyebrow">

            SUA PRÓXIMA EXPERIÊNCIA COMEÇA AQUI

          </span>

          <h1>

            Bom ter você <span>de volta.</span>

          </h1>

          <p>Entre na sua conta para continuar sua experiência de compra.</p>



          <div className="login-orbit">

            <span>SHOP</span>

            <strong>✦</strong>

          </div>

        </div>



        <div className="login-card">

          <span className="eyebrow">ACESSO À CONTA</span>

          <h2>Entrar</h2>

          <p className="login-subtitle">

            Informe seus dados para continuar.

          </p>



          <form onSubmit={handleLogin}>

            <label htmlFor="email">E-mail</label>

            <input

              id="email"

              type="email"

              placeholder="voce@exemplo.com"

              value={email}

              onChange={(event) => setEmail(event.target.value)}

              autoComplete="email"

              required

            />



            <label htmlFor="senha">Senha</label>

            <input

              id="senha"

              type="password"

              placeholder="Digite sua senha"

              value={senha}

              onChange={(event) => setSenha(event.target.value)}

              autoComplete="current-password"

              required

            />



            <div className="login-options">

              <Link to="/recuperar-senha">Esqueci minha senha</Link>

            </div>



            {erro && (

              <p className="form-message error" role="alert">

                {erro}

              </p>

            )}



            {mensagem && (

              <p className="form-message success" role="status">

                {mensagem}

              </p>

            )}



            <button

              className="shop-button login-submit"

              type="submit"

              disabled={carregando}

            >

              {carregando ? 'Entrando...' : 'Entrar na conta →'}

            </button>

          </form>



          <p className="login-note">

            Seus dados são protegidos e utilizados com segurança.

          </p>



          <p className="login-note">

            Ainda não tem uma conta? <Link to="/cadastro">Criar conta</Link>

          </p>

        </div>

      </section>



      <footer>

        <p>

          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.

        </p>

      </footer>

    </main>

  )

}



// ============================================

// MINHA CONTA

// ============================================



function MinhaConta() {

  const navigate = useNavigate()

  const token = sessionStorage.getItem('access_token')



  function handleLogout() {

    sessionStorage.removeItem('access_token')

    navigate('/', { replace: true })

  }



  if (!token) {

    return <Navigate to="/" replace />

  }



  return (

    <main className="store">

      <header className="navbar">

        <Link className="logo" to="/minha-conta">

          e<span>commerce</span>

        </Link>



        <nav className="account-nav">

          <Link to="/minha-conta">Minha conta</Link>

          <Link to="/carrinho">🛒 Meu carrinho</Link>



          <button

            className="shop-button"

            type="button"

            onClick={handleLogout}

          >

            Sair

          </button>

        </nav>

      </header>



      <section className="store-home">

        <div className="store-welcome">

          <span className="eyebrow">ÁREA DO CLIENTE</span>



          <h1>

            Bem-vindo à sua <span>loja.</span>

          </h1>



          <p>

            Explore nossos produtos e encontre seu próximo favorito.

          </p>

        </div>



        <Catalogo />

      </section>



      <footer>

        <p>

          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.

        </p>

      </footer>

    </main>

  )

}



// ============================================

// RECUPERAR SENHA

// ============================================



function RecuperarSenha() {

  const [email, setEmail] = useState('')

  const [erro, setErro] = useState('')

  const [mensagem, setMensagem] = useState('')

  const [carregando, setCarregando] = useState(false)



  async function handleSubmit(event) {

    event.preventDefault()

    setErro('')

    setMensagem('')

    setCarregando(true)



    try {

      const data = await apiRequest('/usuarios/recuperar-senha', {

        method: 'POST',

        body: JSON.stringify({ email }),

      })



      setMensagem(

        data.message ||

          'Se o e-mail estiver cadastrado, você receberá as instruções.',

      )

    } catch (error) {

      setErro(error.message || 'Não foi possível solicitar a recuperação.')

    } finally {

      setCarregando(false)

    }

  }



  return (

    <main className="store">

      <header className="navbar">

        <Link className="logo" to="/">

          e<span>commerce</span>

        </Link>

        <Link className="back-link" to="/">

          Voltar ao login

        </Link>

      </header>



      <section className="login-page reset-page">

        <div className="login-decoration">

          <span className="eyebrow">RECUPERAÇÃO DE CONTA</span>

          <h1>

            Vamos ajudar você a <span>voltar.</span>

          </h1>

          <p>

            Informe o e-mail da sua conta para receber as instruções de

            recuperação.

          </p>



          <div className="login-orbit">

            <span>SECURE</span>

            <strong>✦</strong>

          </div>

        </div>



        <div className="login-card">

          <span className="eyebrow">ACESSO À CONTA</span>

          <h2>Esqueci minha senha</h2>

          <p className="login-subtitle">

            Enviaremos as instruções para o e-mail informado.

          </p>



          <form onSubmit={handleSubmit}>

            <label htmlFor="recuperar-email">E-mail</label>

            <input

              id="recuperar-email"

              type="email"

              placeholder="voce@exemplo.com"

              value={email}

              onChange={(event) => setEmail(event.target.value)}

              autoComplete="email"

              required

            />



            {erro && (

              <p className="form-message error" role="alert">

                {erro}

              </p>

            )}



            {mensagem && (

              <p className="form-message success" role="status">

                {mensagem}

              </p>

            )}



            <button

              className="shop-button login-submit"

              type="submit"

              disabled={carregando}

            >

              {carregando ? 'Enviando...' : 'Enviar instruções →'}

            </button>

          </form>

        </div>

      </section>



      <footer>

        <p>

          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.

        </p>

      </footer>

    </main>

  )

}



// ============================================

// REDEFINIR SENHA

// ============================================



function RedefinirSenha() {

  const [searchParams] = useSearchParams()

  const token = searchParams.get('token')



  const [novaSenha, setNovaSenha] = useState('')

  const [confirmacao, setConfirmacao] = useState('')

  const [erro, setErro] = useState('')

  const [mensagem, setMensagem] = useState('')

  const [carregando, setCarregando] = useState(false)



  async function handleSubmit(event) {

    event.preventDefault()

    setErro('')

    setMensagem('')



    if (!token) {

      setErro(

        'O link de recuperação não contém um token válido. Solicite um novo e-mail.',

      )

      return

    }



    if (novaSenha.length < 8) {

      setErro('A senha deve ter pelo menos 8 caracteres.')

      return

    }



    if (!/[A-Z]/.test(novaSenha)) {

      setErro('A senha deve conter pelo menos uma letra maiúscula.')

      return

    }



    if (!/[^A-Za-z0-9]/.test(novaSenha)) {

      setErro('A senha deve conter pelo menos um caractere especial.')

      return

    }



    if (novaSenha !== confirmacao) {

      setErro('As senhas não coincidem.')

      return

    }



    setCarregando(true)



    try {

      const data = await apiRequest('/usuarios/redefinir-senha', {

        method: 'POST',

        body: JSON.stringify({

          token,

          nova_senha: novaSenha,

        }),

      })



      setMensagem(data.message || 'Senha redefinida com sucesso.')

      setNovaSenha('')

      setConfirmacao('')

    } catch (error) {

      setErro(error.message || 'Não foi possível redefinir a senha.')

    } finally {

      setCarregando(false)

    }

  }



  return (

    <main className="store">

      <header className="navbar">

        <Link className="logo" to="/">

          e<span>commerce</span>

        </Link>

        <Link className="back-link" to="/">

          Voltar ao login

        </Link>

      </header>



      <section className="login-page reset-page">

        <div className="login-decoration">

          <span className="eyebrow">RECUPERAÇÃO DE CONTA</span>

          <h1>

            Uma nova senha, <span>um novo começo.</span>

          </h1>

          <p>Crie uma nova senha segura para voltar a acessar sua conta.</p>



          <div className="login-orbit">

            <span>SECURE</span>

            <strong>✦</strong>

          </div>

        </div>



        <div className="login-card">

          <span className="eyebrow">SEGURANÇA DA CONTA</span>

          <h2>Redefinir senha</h2>

          <p className="login-subtitle">

            Escolha sua nova senha e confirme abaixo.

          </p>



          <p className="password-requirements">

            A senha deve conter:

            <span>• Pelo menos 8 caracteres</span>

            <span>• Uma letra maiúscula (A–Z)</span>

            <span>• Um caractere especial (!@#$%)</span>

          </p>



          <form onSubmit={handleSubmit}>

            <label htmlFor="nova-senha">Nova senha</label>

            <input

              id="nova-senha"

              type="password"

              placeholder="Mínimo de 8 caracteres"

              value={novaSenha}

              onChange={(event) => setNovaSenha(event.target.value)}

              minLength={8}

              maxLength={128}

              autoComplete="new-password"

              required

            />



            <label htmlFor="confirmacao">Confirmar nova senha</label>

            <input

              id="confirmacao"

              type="password"

              placeholder="Digite a senha novamente"

              value={confirmacao}

              onChange={(event) => setConfirmacao(event.target.value)}

              minLength={8}

              maxLength={128}

              autoComplete="new-password"

              required

            />



            {erro && (

              <p className="form-message error" role="alert">

                {erro}

              </p>

            )}



            {mensagem && (

              <p className="form-message success" role="status">

                {mensagem}

              </p>

            )}



            <button

              className="shop-button login-submit"

              type="submit"

              disabled={carregando}

            >

              {carregando ? 'Salvando...' : 'Salvar nova senha →'}

            </button>

          </form>



          <p className="login-note">

            O link é de uso único e expira após 30 minutos.

          </p>



          {mensagem && (

            <p className="login-note">

              <Link to="/">Voltar ao login</Link>

            </p>

          )}

        </div>

      </section>



      <footer>

        <p>

          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.

        </p>

      </footer>

    </main>

  )

}



// ============================================

// CADASTRO

// ============================================



function Cadastro() {

  const [nome, setNome] = useState('')

  const [email, setEmail] = useState('')

  const [senha, setSenha] = useState('')

  const [confirmacao, setConfirmacao] = useState('')

  const [erro, setErro] = useState('')

  const [mensagem, setMensagem] = useState('')

  const [carregando, setCarregando] = useState(false)



  async function handleSubmit(event) {

    event.preventDefault()

    setErro('')

    setMensagem('')



    if (senha.length < 8) {

      setErro('A senha deve ter pelo menos 8 caracteres.')

      return

    }



    if (!/[A-Z]/.test(senha)) {

      setErro('A senha deve conter pelo menos uma letra maiúscula.')

      return

    }



    if (!/[^A-Za-z0-9]/.test(senha)) {

      setErro('A senha deve conter pelo menos um caractere especial.')

      return

    }



    if (senha !== confirmacao) {

      setErro('As senhas não coincidem.')

      return

    }



    setCarregando(true)



    try {

      await apiRequest('/usuarios/', {

        method: 'POST',

        body: JSON.stringify({ nome, email, senha }),

      })



      setMensagem('Conta criada com sucesso! Você já pode entrar.')

      setNome('')

      setEmail('')

      setSenha('')

      setConfirmacao('')

    } catch (error) {

      setErro(error.message || 'Não foi possível criar sua conta.')

    } finally {

      setCarregando(false)

    }

  }



  return (

    <main className="store">

      <header className="navbar">

        <Link className="logo" to="/">

          e<span>commerce</span>

        </Link>

        <Link className="back-link" to="/">

          Voltar ao login

        </Link>

      </header>



      <section className="login-page reset-page">

        <div className="login-decoration">

          <span className="eyebrow">CRIE SUA CONTA</span>

          <h1>

            Sua próxima experiência começa <span>aqui.</span>

          </h1>

          <p>

            Cadastre-se para acessar sua conta e aproveitar a experiência da

            nossa loja.

          </p>



          <div className="login-orbit">

            <span>WELCOME</span>

            <strong>✦</strong>

          </div>

        </div>



        <div className="login-card">

          <span className="eyebrow">NOVO CLIENTE</span>

          <h2>Criar conta</h2>

          <p className="login-subtitle">

            Preencha seus dados para começar.

          </p>



          <form onSubmit={handleSubmit}>

            <label htmlFor="cadastro-nome">Nome</label>

            <input

              id="cadastro-nome"

              type="text"

              placeholder="Seu nome completo"

              value={nome}

              onChange={(event) => setNome(event.target.value)}

              minLength={2}

              maxLength={100}

              autoComplete="name"

              required

            />



            <label htmlFor="cadastro-email">E-mail</label>

            <input

              id="cadastro-email"

              type="email"

              placeholder="voce@exemplo.com"

              value={email}

              onChange={(event) => setEmail(event.target.value)}

              autoComplete="email"

              required

            />



            <label htmlFor="cadastro-senha">Senha</label>

            <input

              id="cadastro-senha"

              type="password"

              placeholder="Crie uma senha segura"

              value={senha}

              onChange={(event) => setSenha(event.target.value)}

              minLength={8}

              maxLength={128}

              autoComplete="new-password"

              required

            />



            <p className="password-requirements">

              A senha deve conter:

              <span>• Pelo menos 8 caracteres</span>

              <span>• Uma letra maiúscula (A–Z)</span>

              <span>• Um caractere especial (!@#$%)</span>

            </p>



            <label htmlFor="cadastro-confirmacao">Confirmar senha</label>

            <input

              id="cadastro-confirmacao"

              type="password"

              placeholder="Digite a senha novamente"

              value={confirmacao}

              onChange={(event) => setConfirmacao(event.target.value)}

              minLength={8}

              maxLength={128}

              autoComplete="new-password"

              required

            />



            {erro && (

              <p className="form-message error" role="alert">

                {erro}

              </p>

            )}



            {mensagem && (

              <p className="form-message success" role="status">

                {mensagem}

              </p>

            )}



            <button

              className="shop-button login-submit"

              type="submit"

              disabled={carregando}

            >

              {carregando ? 'Criando conta...' : 'Criar minha conta →'}

            </button>

          </form>



          <p className="login-note">

            Já tem uma conta? <Link to="/">Entrar</Link>

          </p>

        </div>

      </section>



      <footer>

        <p>

          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.

        </p>

      </footer>

    </main>

  )

}



// ============================================
// PAGAMENTO: SUCESSO E CANCELAMENTO
// ============================================

function PagamentoSucesso() {
  const navigate = useNavigate()

  return (
    <main className="store">
      <header className="navbar">
        <Link className="logo" to="/minha-conta">
          e<span>commerce</span>
        </Link>
      </header>

      <section className="store-home">
        <div className="store-welcome">
          <span className="eyebrow">PAGAMENTO CONFIRMADO</span>
          <h1>
            Obrigado pela sua <span>compra!</span>
          </h1>
          <p>
            Seu pagamento foi processado pelo Stripe. Você pode acompanhar
            seu pedido em breve.
          </p>
          <button
            className="shop-button"
            type="button"
            onClick={() => navigate('/minha-conta')}
          >
            Voltar à loja →
          </button>
        </div>
      </section>

      <footer>
        <p>
          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.
        </p>
      </footer>
    </main>
  )
}

function PagamentoCancelado() {
  const navigate = useNavigate()
  const token = sessionStorage.getItem('access_token')

  return (
    <main className="store">
      <header className="navbar">
        <Link className="logo" to="/minha-conta">
          e<span>commerce</span>
        </Link>
      </header>

      <section className="store-home">
        <div className="store-welcome">
          <span className="eyebrow">PAGAMENTO NÃO CONCLUÍDO</span>
          <h1>Seu pagamento foi cancelado.</h1>
          <p>
            O pagamento não foi concluído. Você pode voltar ao carrinho e
            tentar novamente.
          </p>
          <button
            className="shop-button"
            type="button"
            onClick={() => navigate(token ? '/carrinho' : '/')}
          >
            Voltar ao carrinho →
          </button>
        </div>
      </section>

      <footer>
        <p>
          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.
        </p>
      </footer>
    </main>
  )
}


// ============================================

// ROTAS

// ============================================



function CarrinhoProtegido() {
  const token = sessionStorage.getItem('access_token')

  if (!token) {
    return <Navigate to="/" replace />
  }

  return (
    <main className="store">
      <header className="navbar">
        <Link className="logo" to="/minha-conta">
          e<span>commerce</span>
        </Link>

        <Link className="back-link" to="/minha-conta">
          Voltar à loja
        </Link>
      </header>

      <Carrinho />

      <footer>
        <p>
          © {new Date().getFullYear()} E-commerce. Todos os direitos reservados.
        </p>
      </footer>
    </main>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/carrinho" element={<CarrinhoProtegido />} />
      <Route path="/" element={<Login />} />
      <Route path="/minha-conta" element={<MinhaConta />} />
      <Route path="/recuperar-senha" element={<RecuperarSenha />} />
      <Route path="/redefinir-senha" element={<RedefinirSenha />} />
      <Route path="/cadastro" element={<Cadastro />} />
      <Route path="/pagamento/sucesso" element={<PagamentoSucesso />} />
      <Route path="/pagamento/cancelado" element={<PagamentoCancelado />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App