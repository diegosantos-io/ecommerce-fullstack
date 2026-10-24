import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen} from '@testing-library/react'
import Catalogo from './Catalogo'
import { apiRequest } from '../services/api'

vi.mock('../services/api', () => ({
  apiRequest: vi.fn(),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  sessionStorage.clear()
})

const produtosExemplo = [
  {
    id: 1,
    nome: 'Teclado Mecânico',
    descricao: 'Teclado para jogos',
    preco: 199.9,
    estoque: 5,
    categoria_id: 2,
    ativo: true,
    imagem_url: '',
  },
  {
    id: 2,
    nome: 'Produto Inativo',
    descricao: 'Não deve aparecer',
    preco: 49.9,
    estoque: 10,
    categoria_id: 1,
    ativo: false,
    imagem_url: '',
  },
]

describe('Catálogo de produtos', () => {
  it('mostra o estado de carregamento', () => {
    apiRequest.mockReturnValue(new Promise(() => {}))

    render(<Catalogo />)

    expect(screen.getByText('Carregando produtos...')).toBeInTheDocument()
  })

  it('exibe apenas produtos ativos', async () => {
    apiRequest.mockResolvedValue(produtosExemplo)

    render(<Catalogo />)

    expect(
      await screen.findByRole('heading', { name: 'Teclado Mecânico' }),
    ).toBeInTheDocument()

    expect(screen.queryByText('Produto Inativo')).not.toBeInTheDocument()
  })

  it('formata o preço em reais e mostra o estoque', async () => {
    apiRequest.mockResolvedValue(produtosExemplo)

    render(<Catalogo />)

    expect(await screen.findByText('R$ 199,90')).toBeInTheDocument()
    expect(screen.getByText('5 em estoque')).toBeInTheDocument()
  })

  it('mostra mensagem quando não existem produtos ativos', async () => {
    apiRequest.mockResolvedValue([
      { ...produtosExemplo[1], ativo: false },
    ])

    render(<Catalogo />)

    expect(
      await screen.findByText('Nenhum produto disponível no momento.'),
    ).toBeInTheDocument()
  })

  it('mostra erro quando a API falha', async () => {
    apiRequest.mockRejectedValue(new Error('Falha ao carregar produtos'))

    render(<Catalogo />)

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent('Falha ao carregar produtos')
  })
})
