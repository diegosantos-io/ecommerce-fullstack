
import { useEffect, useState } from 'react'
import { apiRequest } from '../services/api'

function formatarPreco(preco) {
  return Number(preco).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

export default function Catalogo() {
  const [produtos, setProdutos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [adicionando, setAdicionando] = useState(null)
  const [mensagem, setMensagem] = useState('')

  useEffect(() => {
    let ativo = true

    async function carregarProdutos() {
      try {
        const dados = await apiRequest('/produtos/')

        if (ativo) {
          setProdutos(dados.filter((produto) => produto.ativo))
        }
      } catch (error) {
        if (ativo) {
          setErro(error.message || 'Não foi possível carregar os produtos.')
        }
      } finally {
        if (ativo) {
          setCarregando(false)
        }
      }
    }

    carregarProdutos()

    return () => {
      ativo = false
    }
  }, [])

  async function adicionarAoCarrinho(produto) {
    setErro('')
    setMensagem('')
    setAdicionando(produto.id)

    try {
      const token = sessionStorage.getItem('access_token')

      if (!token) {
        setErro('Faça login para adicionar produtos ao carrinho.')
        return
      }

      await apiRequest('/carrinho/itens', {
        method: 'POST',
        body: JSON.stringify({
          produto_id: produto.id,
          quantidade: 1,
        }),
      })

      setMensagem(`${produto.nome} foi adicionado ao carrinho!`)
    } catch (error) {
      setErro(error.message || 'Não foi possível adicionar o produto.')
    } finally {
      setAdicionando(null)
    }
  }

  return (
    <section className="catalogo">
      <div className="catalogo-heading">
        <span className="eyebrow">NOSSA SELEÇÃO</span>
        <h2>Produtos em destaque<span>.</span></h2>
        <p>Encontre seu próximo favorito.</p>
      </div>

      {carregando && (
        <p className="catalogo-status">Carregando produtos...</p>
      )}

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

      {!carregando && !erro && produtos.length === 0 && (
        <p className="catalogo-status">
          Nenhum produto disponível no momento.
        </p>
      )}

      {!carregando && produtos.length > 0 && (
        <div className="catalogo-grid">
          {produtos.map((produto) => (
            <article className="produto-card" key={produto.id}>
              <div className="produto-imagem">
                {produto.imagem_url ? (
                  <img
                    src={produto.imagem_url}
                    alt={produto.nome}
                    loading="lazy"
                    onError={(event) => {
                      event.currentTarget.style.display = 'none'
                    }}
                  />
                ) : (
                  <span className="produto-sem-imagem">✦</span>
                )}
              </div>

              <div className="produto-info">
                <span className="produto-categoria">
                  Produto #{produto.categoria_id}
                </span>

                <h3>{produto.nome}</h3>

                <p className="produto-descricao">
                  {produto.descricao || 'Confira os detalhes deste produto.'}
                </p>

                <div className="produto-rodape">
                  <strong>{formatarPreco(produto.preco)}</strong>
                  <span className="produto-estoque">
                    {produto.estoque > 0
                      ? `${produto.estoque} em estoque`
                      : 'Indisponível'}
                  </span>
                </div>

                <button
                  className="shop-button produto-botao"
                  type="button"
                  disabled={produto.estoque <= 0 || adicionando === produto.id}
                  onClick={() => adicionarAoCarrinho(produto)}
                >
                  {produto.estoque <= 0
                    ? 'Indisponível'
                    : adicionando === produto.id
                      ? 'Adicionando...'
                      : 'Adicionar ao carrinho →'}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
