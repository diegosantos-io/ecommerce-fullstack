
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../services/api'

function formatarPreco(valor) {
  return Number(valor).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

export default function Carrinho() {
  const [itens, setItens] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [itemAtualizando, setItemAtualizando] = useState(null)
  const [erro, setErro] = useState('')
  const [mensagem, setMensagem] = useState('')
  const [finalizando, setFinalizando] = useState(false)

  useEffect(() => {
    let cancelado = false

    async function iniciar() {
      try {
        const [carrinho, produtos] = await Promise.all([
          apiRequest('/carrinho/'),
          apiRequest('/produtos/'),
        ])

        if (cancelado) return

        const produtosPorId = new Map(
          produtos.map((produto) => [produto.id, produto]),
        )

        const itensComProduto = carrinho.itens.map((item) => ({
          ...item,
          produto: produtosPorId.get(item.produto_id) || null,
        }))

        setItens(itensComProduto)
      } catch (error) {
        if (!cancelado) {
          setErro(
            error.message || 'Não foi possível carregar o carrinho.',
          )
        }
      } finally {
        if (!cancelado) {
          setCarregando(false)
        }
      }
    }

    iniciar()

    return () => {
      cancelado = true
    }
  }, [])

  async function alterarQuantidade(item, quantidade) {
    if (quantidade < 1) return

    if (item.produto && quantidade > item.produto.estoque) {
      setErro('A quantidade solicitada ultrapassa o estoque disponível.')
      return
    }

    setErro('')
    setMensagem('')
    setItemAtualizando(item.id)

    try {
      await apiRequest(`/carrinho/itens/${item.id}`, {
        method: 'PUT',
        body: JSON.stringify({ quantidade }),
      })

      setItens((atuais) =>
        atuais.map((atual) =>
          atual.id === item.id
            ? { ...atual, quantidade }
            : atual,
        ),
      )

      setMensagem('Quantidade atualizada com sucesso.')
    } catch (error) {
      setErro(
        error.message || 'Não foi possível atualizar a quantidade.',
      )
    } finally {
      setItemAtualizando(null)
    }
  }

  async function removerItem(item) {
    setErro('')
    setMensagem('')
    setItemAtualizando(item.id)

    try {
      await apiRequest(`/carrinho/itens/${item.id}`, {
        method: 'DELETE',
      })

      setItens((atuais) =>
        atuais.filter((atual) => atual.id !== item.id),
      )

      setMensagem('Produto removido do carrinho.')
    } catch (error) {
      setErro(
        error.message || 'Não foi possível remover o produto.',
      )
    } finally {
      setItemAtualizando(null)
    }
  }
 
  
  async function finalizarCompra() {
    setErro('')
    setMensagem('')

    if (itens.length === 0) {
        setErro('Seu carrinho está vazio.')
        return
    }

    setFinalizando(true)

    try {
        // Cria o pedido usando os preços e quantidades validados pelo backend.
        const pedido = await apiRequest('/pedidos/', {
          method: 'POST',
        })

        if (!pedido?.id) {
          throw new Error('O backend não retornou o número do pedido.')
        }

        // Cria a sessão de pagamento para esse pedido.
        const checkout = await apiRequest(
          `/pagamentos/checkout/${pedido.id}`,
          {
            method: 'POST',
          },
        )

        if (!checkout?.checkout_url) {
          throw new Error('O Stripe não retornou a URL de pagamento.')
        }

        // Redireciona o cliente para o Stripe Checkout.
        window.location.assign(checkout.checkout_url)
      } catch (error) {
        setErro(
          error.message ||
            'Não foi possível iniciar o pagamento. Tente novamente.',
    )
    setFinalizando(false)
  }
}


  const subtotal = itens.reduce((total, item) => {
    return (
      total +
      Number(item.produto?.preco || 0) * item.quantidade
    )
  }, 0)

  const quantidadeTotal = itens.reduce(
    (total, item) => total + item.quantidade,
    0,
  )

  return (
    <section className="carrinho-page">
      <div className="carrinho-heading">
        <span className="eyebrow">SUA SELEÇÃO</span>
        <h1>
          Meu carrinho<span>.</span>
        </h1>
        <p>Confira seus produtos antes de continuar.</p>
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

      {carregando ? (
        <p className="catalogo-status">
          Carregando seu carrinho...
        </p>
      ) : itens.length === 0 ? (
        <div className="carrinho-vazio">
          <span className="carrinho-vazio-icone">🛒</span>
          <h2>Seu carrinho está vazio</h2>
          <p>
            Explore a loja e adicione seus produtos favoritos.
          </p>

          <Link
            className="shop-button carrinho-voltar"
            to="/minha-conta"
          >
            Continuar comprando →
          </Link>
        </div>
      ) : (
        <>
          <div className="carrinho-lista">
            {itens.map((item) => (
              <article
                className="carrinho-item"
                key={item.id}
              >
                <div className="carrinho-item-imagem">
                  {item.produto?.imagem_url ? (
                    <img
                      src={item.produto.imagem_url}
                      alt={item.produto.nome}
                      loading="lazy"
                    />
                  ) : (
                    <span>✦</span>
                  )}
                </div>

                <div className="carrinho-item-info">
                  <h2>
                    {item.produto?.nome ||
                      `Produto #${item.produto_id}`}
                  </h2>

                  <p>
                    {item.produto
                      ? formatarPreco(item.produto.preco)
                      : 'Preço indisponível'}
                  </p>

                  {item.produto &&
                    item.quantidade > item.produto.estoque && (
                      <p className="carrinho-aviso">
                        Quantidade acima do estoque atual.
                      </p>
                    )}

                  <div className="carrinho-acoes">
                    <div
                      className="quantidade-controle"
                      aria-label="Quantidade do produto"
                    >
                      <button
                        type="button"
                        aria-label="Diminuir quantidade"
                        disabled={
                          itemAtualizando === item.id ||
                          item.quantidade <= 1
                        }
                        onClick={() =>
                          alterarQuantidade(
                            item,
                            item.quantidade - 1,
                          )
                        }
                      >
                        −
                      </button>

                      <span>{item.quantidade}</span>

                      <button
                        type="button"
                        aria-label="Aumentar quantidade"
                        disabled={
                          itemAtualizando === item.id ||
                          Boolean(
                            item.produto &&
                              item.quantidade >=
                                item.produto.estoque,
                          )
                        }
                        onClick={() =>
                          alterarQuantidade(
                            item,
                            item.quantidade + 1,
                          )
                        }
                      >
                        +
                      </button>
                    </div>

                    <button
                      className="carrinho-remover"
                      type="button"
                      disabled={itemAtualizando === item.id}
                      onClick={() => removerItem(item)}
                    >
                      {itemAtualizando === item.id
                        ? 'Aguarde...'
                        : 'Remover'}
                    </button>
                  </div>
                </div>

                <strong className="carrinho-item-total">
                  {formatarPreco(
                    Number(item.produto?.preco || 0) *
                      item.quantidade,
                  )}
                </strong>
              </article>
            ))}
          </div>

          <aside className="carrinho-resumo">
            <h2>Resumo do pedido</h2>

            <div className="carrinho-resumo-linha">
              <span>Itens</span>
              <span>{quantidadeTotal}</span>
            </div>

            <div className="carrinho-resumo-linha">
              <span>Subtotal</span>
              <strong>{formatarPreco(subtotal)}</strong>
            </div>

            <p className="carrinho-nota">
              Frete e pagamento serão calculados na próxima etapa.
            </p>

            <button
              className="shop-button carrinho-finalizar"
              type="button"
              disabled = {finalizando || carregando || itens.length === 0}
              onClick={finalizarCompra}
            >
              {finalizando
                ? 'Preparando pagamento...'
                : 'Finalizar compra →'}
            </button>

            <Link
              className="carrinho-continuar"
              to="/minha-conta"
            >
              ← Continuar comprando
            </Link>
          </aside>
        </>
      )}

      {!carregando && itens.length > 0 && (
        <Link
          className="carrinho-continuar carrinho-link-final"
          to="/minha-conta"
        >
          ← Voltar à loja
        </Link>
      )}
    </section>
  )
}
